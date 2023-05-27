import io

from django.utils import timezone
from django.contrib import admin
from django.db import models
from PIL import Image, ImageDraw, ImageFont
from django.core.files import File

from accounts.models import Profile


def process_image(img, text=None, ext='png', font_type='arial.ttf', font_size=32, new_height=None, new_width=None):
    image = Image.open(img)

    width, height = image.size
    if new_width:
        new_height = int(height * new_width / width)
    elif new_height:
        new_width = int(width * new_height / height)

    if new_width and new_height:
        image.resize((new_width, new_height))

    # if text:
    #     img_draw = ImageDraw.Draw(image)
    #     font = ImageFont.truetype(font_type, size=font_size)
    #     img_draw.text((10, 10), text, font=font)

    image_io = io.BytesIO()
    image.save(image_io, ext)
    return File(image_io, f'image.{ext}')

def tweet_image_store(instance, filename):
    return f'profile/{instance.profile.user.username}/{timezone.now().strftime("%Y%m%d_%H%M")}/{filename}'


class Tweet(models.Model):
    text = models.CharField(max_length=140)
    image = models.ImageField(upload_to=tweet_image_store, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile = models.ForeignKey(Profile, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Твит"
        verbose_name_plural = "Твиты"

    def save(self, *args, **kwargs):
        if self.image:
            self.image = process_image(self.image, text='Property of me', font_size=24)
        super().save(*args, **kwargs)

    def all_reactions(self):
        result = {}
        for rtype in ReactionType.objects.all():
            result[rtype.name] = 0
        for reaction in self.reactions.all():
            result[reaction.reaction.name] += 1

        return result

    def get_reactions(self):
        reactions = self.reactions.all()
        result = {}
        for reaction in reactions:
            if result.get(reaction.reaction.name):
                result[reaction.reaction.name] += 1
            else:
                result[reaction.reaction.name] = 1

        return result

    @admin.display(description='reactions')
    def get_reactions_str(self):
        reactions = self.get_reactions()
        return str(reactions)

    def __str__(self):
        return self.text


class Reply(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    text = models.CharField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile = models.ForeignKey(Profile, on_delete=models.PROTECT)

    def get_reactions(self):
        reactions = self.reply_reactions.all()
        result = {}
        for reaction in reactions:
            if result.get(reaction.reaction.name):
                result[reaction.reaction.name] += 1
            else:
                result[reaction.reaction.name] = 1
        return result

    def __str__(self):
        return self.text


class ReactionType(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Reaction(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='reactions')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    reaction = models.ForeignKey(ReactionType, on_delete=models.SET_DEFAULT, default=1)

    def __str__(self):
        return f'{self.tweet} - {self.profile} - {self.reaction}'

    class Meta:
        unique_together = ['tweet', 'profile']


class ReplyReaction(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name='reply_reactions')
    reaction = models.ForeignKey(ReactionType, on_delete=models.SET_DEFAULT, default=1)

    def __str__(self):
        return self.reply

    class Meta:
        unique_together = ['profile', 'reply']


def tweet_multiple_images_store(instance, filename):
    return f'profile/{instance.tweet.profile.user.username}/{instance.tweet.id}/{filename}'


class TweetImages(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=tweet_multiple_images_store)
