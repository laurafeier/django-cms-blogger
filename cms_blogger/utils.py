from django.utils.encoding import smart_unicode


def user_display_name(user):
    if user.first_name and user.last_name:
        return u'%s %s' % (self.author.first_name, user.last_name)
    elif user.email:
        return user.email
    else:
        return smart_unicode(self.author)
