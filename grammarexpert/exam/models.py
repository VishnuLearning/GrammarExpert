from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    BRANCH_CHOICES = (
        ('CSE', 'Computer Science and Engineering'),
        ('ECE', 'Electronics and Communication'),
        ('EEE', 'Electrical and Electronics Engineering'),
        ('ME', 'Mechanical Engineering'),
        ('CE', 'Civil Engineering'),
        ('CHE', 'Chemical Engineering'),
        ('IT', 'Information Technology'),
        ('PHM', 'Pharmacy')
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    college = models.CharField(max_length=250, blank=False)
    college_id = models.CharField(max_length=20, blank=False)
    branch_of_study = models.CharField(max_length=3, blank=False, choices=BRANCH_CHOICES)
    name = models.CharField(max_length=100, blank=False)
    class Meta:
        permissions = (
            ("create_test", "Can create tests"),
        )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
    

class Question(models.Model):
    QUESTION_TYPES = (
        ('ES', 'Essay'),
        ('PS', 'Picture Story'),
        ('CP', 'Connect the phrases'),
        ('UW', 'Use words')
    )
    question = models.CharField(max_length = 500)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length = 8,unique = True)
    word_limit = models.IntegerField(default=300)
    min_word_count = models.IntegerField(default=150)
    max_word_count_penalty = models.IntegerField(default=3)
    max_word_length_penalty = models.IntegerField(default=2)
    desired_mean_word_length = models.IntegerField(default=8)
    desired_mean_words_per_sentence = models.IntegerField(default=20)
    max_words_per_sentence_penalty = models.IntegerField(default=2)
    attempts_allowed = models.IntegerField(default=1)
    date_created = models.DateField(default=datetime.now)
    time_limit = models.IntegerField(default=30)
    question_type = models.CharField(max_length=2, blank=False, choices=QUESTION_TYPES, default='ES')
    keywords = models.TextField(default="", blank=True)
    expanded_keywords = models.TextField(default="", blank=True)
    picture = models.ImageField(default="/standard/es.jpg")
    # to add keywords, picture essay image, tags, question type (essay, picture essay, connect phrases, use words etc.)
    # would need separate checking algorithm for each

    def __str__(self):
        return "{}".format(self.question)


class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    score = models.FloatField()
    Json = models.TextField()
    spellingErrors = models.IntegerField()
    grammarErrors = models.IntegerField()
    starttime = models.DateTimeField()
    endtime = models.DateTimeField()
    comments = models.CharField(max_length=255, default="")
