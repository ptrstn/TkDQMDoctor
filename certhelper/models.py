"""
Models define the database schema and the data that is stored in the database.
For (most) of the models there is a corresponding FORM so that it is possible
for users to add data to the model and to display it
TkDQMDoctor/dqmsite/certhelper/forms.py.
i.e

FORM               |  MODEL
====================================
ReferenceRunForm   |  ReferenceRun
RunInfoForm        |  RunInfo
TypeForm           |  Type


"""
import logging

from allauth.socialaccount.fields import JSONField
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from certhelper.manager import SoftDeletionManager, RunInfoManager
from certhelper.utilities.logger import get_configured_logger
from certhelper.utilities.utilities import get_full_name


logger = get_configured_logger(loggername=__name__, filename="models.log")

RECO_CHOICES = (('Express', 'Express'), ('Prompt', 'Prompt'), ('reReco', 'reReco'))
RUNTYPE_CHOICES = (('Cosmics', 'Cosmics'), ('Collisions', 'Collisions'))
BFIELD_CHOICES = (('0 T', '0 T'), ('3.8 T', '3.8 T'))
BEAMTYPE_CHOICES = (('Cosmics', 'Cosmics'), ('Proton-Proton', 'Proton-Proton'), ('HeavyIon-Proton', 'HeavyIon-Proton'),
                    ('HeavyIon-HeavyIon', 'HeavyIon-HeavyIon'))
BEAMENERGY_CHOICES = (('Cosmics', 'Cosmics'), ('5 TeV', '5 TeV'), ('13 TeV', '13 TeV'))


class UserProfile(models.Model):
    """
    Do NOT instantiate this manually!
    It will be automatically created/updated when a User instance is created/updated

    - adds extra information to the django User model
    - extends the default django User model using signals
    - grants user more access rights based on CERN e-groups the user is member of
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    GUEST = 0
    SHIFTER = 10
    SHIFTLEADER = 20
    EXPERT = 30
    ADMIN = 50

    USER_PRIVILEGE_CHOICES = (
        (GUEST, 'Guest'),
        (SHIFTER, 'Shifter'),
        (SHIFTLEADER, "Shift Leader"),
        (EXPERT, "Expert"),
        (ADMIN, "Administrator"),
    )

    SHIFT_LEADER_GROUP_NAME = "Shift leaders"

    """
    Dictionary containing which e-group a user has to be member of, in order to 
    to gain a specific user privilege (e.g. Shift Leader or Admin)
    """
    criteria_groups_dict = {
        SHIFTER: [
            "tkdqmdoctor-shifters",
        ],
        SHIFTLEADER: [
            "cms-tracker-offline-shiftleader",
            "cms-tracker-offline-shiftleaders",
            "tkdqmdoctor-shiftleaders",
        ],
        EXPERT: [
            "tkdqmdoctor-experts",
        ],
        ADMIN: [
            "tkdqmdoctor-admins",
        ]
    }

    extra_data = JSONField(verbose_name='extra data', default=dict)

    user_privilege = models.IntegerField(choices=USER_PRIVILEGE_CHOICES, default=GUEST)

    def upgrade_user_privilege(self):
        """
        Does upgrade a user privilege if the user is inside a higher privilege e-group
        Does NOT downgrade a status, i.e. once a shift leader always a shift leader
        """
        try:
            egroups = self.extra_data.get("groups")
            logger.debug("extra_data = {}".format(self.extra_data))
            logger.debug("egroups = {}".format(self.extra_data.get("groups")))
            assert egroups is not None

            for user_privilege, necessary_group_list in self.criteria_groups_dict.items():
                logger.debug("user_privilege = {}, necessary_group_list = {}".format(user_privilege, necessary_group_list))
                if any(egroup in necessary_group_list for egroup in egroups):
                    logger.debug("Criteria matched for user_privilege {}, self.user_privilege={}".format(user_privilege, self.user_privilege))
                    logger.debug("Checked group list for privilege {} is {}".format(user_privilege, necessary_group_list))
                    if self.user_privilege < user_privilege:
                        self.user_privilege = user_privilege
                        logger.info("User {} has been granted {} status".format(
                            self.user, self.get_user_privilege_display()))
                        if self.user_privilege == self.ADMIN:
                            self.user.is_superuser = True
                            logger.info("User {} is now superuser".format(self.user))
                        if self.user_privilege >= self.SHIFTLEADER:
                            self.user.is_staff = True
                            try:
                                g = Group.objects.get(name=self.SHIFT_LEADER_GROUP_NAME)
                                self.user.groups.add(g)
                                logger.info("User {} has been added to Group {}".format(self.user, self.SHIFT_LEADER_GROUP_NAME))
                            except Group.DoesNotExist:
                                logger.error("Group {} does not exist".format(self.SHIFT_LEADER_GROUP_NAME))
                                user_permissions = Permission.objects.filter(content_type__model="user")
                                certhelper_permissions = Permission.objects.filter(content_type__app_label="certhelper")
                                g = Group.objects.create(name=self.SHIFT_LEADER_GROUP_NAME)
                                for permission in user_permissions:
                                    g.permissions.add(permission)
                                for permission in certhelper_permissions:
                                    g.permissions.add(permission)
                                g.save()
                                logger.error("Group {} has been created".format(self.SHIFT_LEADER_GROUP_NAME))
                                self.user.groups.add(g)
                                logger.info("User {} has been added to Group {}".format(self.user, self.SHIFT_LEADER_GROUP_NAME))

                            logger.info("User {} is now staff".format(self.user))
                    else:
                        logger.debug("Privilege not updated because it is already higher user_privilege={}, "
                                     "self.user_privilege={}".format(user_privilege, self.user_privilege))
        except AssertionError:
            logger.error("No e-groups found")
        except Exception as e:
            logger.error("Failed to upgrade user privilege")
            logger.exception(e)

    @property
    def is_guest(self):
        return self.user_privilege == self.GUEST

    @property
    def is_shifter(self):
        return self.user_privilege == self.SHIFTER

    @property
    def is_shiftleader(self):
        return self.user_privilege == self.SHIFTLEADER

    @property
    def is_expert(self):
        return self.user_privilege == self.EXPERT

    @property
    def is_admin(self):
        return self.user_privilege == self.ADMIN

    @property
    def has_shifter_rights(self):
        return self.user_privilege in (self.SHIFTER, self.SHIFTLEADER, self.EXPERT, self.ADMIN) \
               or self.user.is_staff or self.user.is_superuser

    @property
    def has_shift_leader_rights(self):
        return self.user_privilege in (self.SHIFTLEADER, self.EXPERT, self.ADMIN) \
               or self.user.is_staff or self.user.is_superuser


class SoftDeletionModel(models.Model):
    """
    Marks object as deleted rather than irrevocably deleting that object
    Also adds timestamps for creation time and update time

    check https://medium.com/@adriennedomingus/soft-deletion-in-django-e4882581c340 for further information
    """
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeletionManager()
    all_objects = SoftDeletionManager(alive_only=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super(SoftDeletionModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super(SoftDeletionModel, self).delete()

    def restore(self):
        self.deleted_at = None
        self.save()


class Category(SoftDeletionModel):
    name = models.CharField(max_length=30, help_text="Title for the category of problems found")

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return str(self.name)


# TODO make parent_category not nullable
class SubCategory(SoftDeletionModel):
    name = models.CharField(max_length=30)
    parent_category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return str(self.name)


# TODO make parent_category not nullable
class SubSubCategory(SoftDeletionModel):
    name = models.CharField(max_length=30)
    parent_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return str(self.name)


class Type(SoftDeletionModel):
    reco = models.CharField(max_length=30, choices=RECO_CHOICES)  # Express, Prompt, reReco
    runtype = models.CharField(max_length=30, choices=RUNTYPE_CHOICES)  # Cosmics, Collisions
    bfield = models.CharField(max_length=30, choices=BFIELD_CHOICES)
    beamtype = models.CharField(max_length=30, choices=BEAMTYPE_CHOICES)
    beamenergy = models.CharField(max_length=10, choices=BEAMENERGY_CHOICES)
    dataset = models.CharField(max_length=150)

    class Meta:
        unique_together = ["reco", "runtype", "bfield", "beamtype", "beamenergy", "dataset"]

    def __str__(self):
        return str(self.reco) + " " + str(self.runtype) + " " + str(self.bfield) + " " + str(self.beamtype) + " " + str(
            self.beamenergy) + " " + str(self.dataset)


# ReferenceRun that should only be added by shift-leaders / staff
class ReferenceRun(SoftDeletionModel):
    reference_run = models.IntegerField()
    reco = models.CharField(max_length=30, choices=RECO_CHOICES)
    runtype = models.CharField(max_length=30, choices=RUNTYPE_CHOICES)
    bfield = models.CharField(max_length=30, choices=BFIELD_CHOICES)
    beamtype = models.CharField(max_length=30, choices=BEAMTYPE_CHOICES)
    beamenergy = models.CharField(max_length=10, choices=BEAMENERGY_CHOICES)
    dataset = models.CharField(max_length=150)

    class Meta:
        unique_together = ["reference_run", "reco", "runtype", "bfield", "beamtype", "beamenergy", "dataset"]
        ordering = ('-reference_run',)

    def __str__(self):
        return str(self.reference_run) + " " + str(self.reco) + " " + str(self.runtype) + " " + str(
            self.bfield) + " " + str(self.beamtype) + " " + str(self.beamenergy) + " " + str(self.dataset)


# Runs that shifters are certifying
class RunInfo(SoftDeletionModel):
    objects = RunInfoManager()
    all_objects = RunInfoManager(alive_only=False)

    GOOD_BAD_CHOICES = (('Good', 'Good'), ('Bad', 'Bad'), ('Lowstat', 'Lowstat'), ('Excluded', 'Excluded'))
    TRACKERMAP_CHOICES = (('Exists', 'Exists'), ('Missing', 'Missing'))
    userid = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    type = models.ForeignKey(Type, on_delete=models.CASCADE)
    reference_run = models.ForeignKey(ReferenceRun, on_delete=models.CASCADE)
    run_number = models.PositiveIntegerField()
    trackermap = models.CharField(max_length=7, choices=TRACKERMAP_CHOICES)
    number_of_ls = models.PositiveIntegerField()
    int_luminosity = models.DecimalField(max_digits=20, decimal_places=2)
    pixel = models.CharField(max_length=10, choices=GOOD_BAD_CHOICES)
    sistrip = models.CharField(max_length=10, choices=GOOD_BAD_CHOICES)
    tracking = models.CharField(max_length=10, choices=GOOD_BAD_CHOICES)
    comment = models.TextField(blank=True)
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    subsubcategory = models.ForeignKey(SubSubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    problem_categories = models.ManyToManyField('categories.Category', blank=True)

    class Meta:
        ordering = ('-run_number',)

    def __str__(self):
        return str(self.run_number) + ", " + str(self.type.runtype) + " " + str(self.type.reco) + \
               " (ref: " + str(self.reference_run.reference_run) + ", " + \
               str(self.reference_run.runtype) + " " + str(self.reference_run.reco) + ")"

    def is_good(self):
        assert self.type.runtype in ['Cosmics', 'Collisions']
        good_criteria = ['Good', 'Lowstat']
        candidates = [self.sistrip, self.tracking]
        if self.type.runtype == 'Collisions':
            candidates.append(self.pixel)

        for candidate in candidates:
            if candidate not in good_criteria:
                return False
        return True

    def is_bad(self):
        return not self.is_good()

    def flag_has_changed(self):
        """
        Checks whether or not the flag from Express to Prompt has changed.

        If a run with run_number x has been certified in Express and this run
        has the type Prompt, then this function returns True if the flag has
        changed (i.e. is_good -> is_bad, or is_bad -> is_good) otherwise False.

        For Example:
        This run has the run_number 42 and was certified with the type Express.
        Another certication for the run_number 42 exists for the type Prompt

        If the other certification is marked good and this run is marked bad
        then the flag has changed and there this function returns True.
        """
        if self.type.reco == "Prompt":
            try:
                express_run = RunInfo.objects.get(type__reco="Express", run_number=self.run_number)
                return self.is_good() != express_run.is_good()
            except RunInfo.DoesNotExist:
                logger.warning("Certification for run_number {} exists for Prompt but not Express!".format(self.run_number))
                return False
            except RunInfo.MultipleObjectsReturned:
                logger.error("More than 2 Express certifications exist for run {}".format(self.run_number))
                logger.info("Checking if all express runs have the same good/bad status")
                express_runs = RunInfo.objects.filter(type__reco="Express", run_number=self.run_number)
                for run in express_runs:
                    if express_runs[0].is_good() != run.is_good():
                        logger.error("Contradiction detected. Cannot unambiguously determine if the flag has changed")
                        return False
                return self.is_good() != express_runs[0].is_good()
        elif self.type.reco == "Express":
            """Check if the Prompt certification has been done before the Express"""
            try:
                prompt_run = RunInfo.objects.get(type__reco="Prompt", run_number=self.run_number)
                return self.is_good() != prompt_run.is_good()
            except RunInfo.DoesNotExist:
                """Most common case, just return False"""
                return False
            except RunInfo.MultipleObjectsReturned:
                logger.error("More than 2 Prompt certifications exist for run {}".format(self.run_number))
                logger.info("Checking if all prompt runs have the same good/bad status")
                prompt_runs = RunInfo.objects.filter(type__reco="Prompt", run_number=self.run_number)
                for run in prompt_runs:
                    if prompt_runs[0].is_good() != run.is_good():
                        logger.error("Contradiction detected. Cannot unambiguously determine if the flag has changed")
                        return False
                return self.is_good() != prompt_runs[0].is_good()
        return False

    def validate_unique(self, exclude=None):
        if not self.type_id:
            raise ValidationError("Type is empty")

        qs = RunInfo.objects.filter(
            run_number=self.run_number,
            type=self.type,
            reference_run=self.reference_run
        )

        # If noone else certified the run and I am not editing the Run
        if qs.exists() and qs[0].pk != self.pk:
            if len(qs) != 1:
                # TODO Logging Warning, duplicate certification
                pass
            run = qs[0]
            raise ValidationError(
                'This run ({}, {} {}, (ref: {})) was already certified by {} on {}'.format(
                    run.run_number,
                    run.type.runtype,
                    run.type.reco,
                    run.reference_run.reference_run,
                    get_full_name(run.userid),
                    run.date)
            )

    def save(self):
        self.validate_unique()
        super(RunInfo, self).save()
