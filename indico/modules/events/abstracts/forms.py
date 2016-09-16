# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import BooleanField, IntegerField, StringField, TextAreaField, HiddenField
from wtforms.validators import NumberRange, Optional, DataRequired

from indico.modules.events.abstracts.fields import AbstractPersonLinkListField
from indico.modules.events.abstracts.settings import BOASortField, BOACorrespondingAuthorType
from indico.modules.events.tracks.models.tracks import Track
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (PrincipalListField, IndicoEnumSelectField, IndicoMarkdownField,
                                     IndicoQuerySelectMultipleCheckboxField)
from indico.web.forms.validators import HiddenUnless
from indico.web.forms.widgets import SwitchWidget, DropzoneWidget


class AbstractContentSettingsForm(IndicoForm):
    """Configure the content field of abstracts"""

    is_active = BooleanField(_('Active'), widget=SwitchWidget(),
                             description=_("Whether the content field is available."))
    is_required = BooleanField(_('Required'), widget=SwitchWidget(),
                               description=_("Whether the user has to fill the content field."))
    max_length = IntegerField(_('Max length'), [Optional(), NumberRange(min=1)])
    max_words = IntegerField(_('Max words'), [Optional(), NumberRange(min=1)])


class BOASettingsForm(IndicoForm):
    """Settings form for the 'Book of Abstracts'"""

    extra_text = IndicoMarkdownField(_('Additional text'), editor=True, mathjax=True)
    sort_by = IndicoEnumSelectField(_('Sort by'), [DataRequired()], enum=BOASortField, sorted=True)
    corresponding_author = IndicoEnumSelectField(_('Corresponding author'), [DataRequired()],
                                                 enum=BOACorrespondingAuthorType, sorted=True)
    show_abstract_ids = BooleanField(_('Show abstract IDs'), widget=SwitchWidget(),
                                     description=_("Show abstract IDs in the table of contents."))


class AbstractSubmissionSettingsForm(IndicoForm):
    """Settings form for abstract submission"""

    announcement = IndicoMarkdownField(_('Announcement'), editor=True)
    allow_multiple_tracks = BooleanField(_('Multiple tracks'), widget=SwitchWidget())
    tracks_required = BooleanField(_('Require tracks'), widget=SwitchWidget())
    allow_attachments = BooleanField(_('Allow attachments'), widget=SwitchWidget())
    allow_speakers = BooleanField(_('Allow speakers'), widget=SwitchWidget())
    speakers_required = BooleanField(_('Require a speaker'), [HiddenUnless('allow_speakers')], widget=SwitchWidget())
    authorized_submitters = PrincipalListField(_("Authorized submitters"),
                                               description=_("These users may always submit abstracts, even outside "
                                                             "the regular submission period."))


class AbstractForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired()])
    description = IndicoMarkdownField(_('Content'), [DataRequired()], editor=True, mathjax=True)
    submitted_contrib_type = QuerySelectField(_("Type"), get_label='name', allow_blank=True,
                                              blank_text=_("No type selected"))
    person_links = AbstractPersonLinkListField(_("People"), [DataRequired()])
    submitted_for_tracks = IndicoQuerySelectMultipleCheckboxField(_("Tracks"), get_label=lambda x: x.title,
                                                                  collection_class=set)
    submission_comment = TextAreaField(_("Comments"))
    attachments = HiddenField(_('Attachments'), widget=DropzoneWidget(style='thin'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.abstract = kwargs.pop('abstract', None)
        super(AbstractForm, self).__init__(*args, **kwargs)
        self.submitted_contrib_type.query = self.event.contribution_types
        if not self.submitted_contrib_type.query.count():
            del self.submitted_contrib_type
        self.submitted_for_tracks.query = Track.query.with_parent(self.event).order_by(Track.title)
        tpl = get_template_module('forms/_dropzone_themes.html')
        self.attachments.widget.options['previewTemplate'] = tpl.thin_preview_template()
        self.attachments.widget.options['dictRemoveFile'] = tpl.remove_icon()
