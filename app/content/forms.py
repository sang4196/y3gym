from django import forms
from django.core.exceptions import ValidationError
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.images.forms import BaseImageForm
from wagtail.images.permissions import permission_policy

class ImmutableImageForm(BaseImageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and 'file' in self.fields:
            self.fields['file'].disabled = True
            self.fields['file'].help_text = '새 사진을 업로드한 후 사용처에서 선택하세요. 기존 파일은 교체할 수 없습니다.'
    def clean(self):
        data = super().clean()
        if self.instance.pk and self.add_prefix('file') in self.files:
            raise ValidationError('기존 파일을 덮어쓸 수 없습니다. 새 자산을 업로드하세요.')
        return data

class ContentForm(WagtailAdminModelForm):
    def clean(self):
        data = super().clean()
        # Reject tampered inline IDs explicitly, including DELETE-marked forms.
        for prefix, formset in self.formsets.items():
            allowed = {str(obj.pk) for obj in formset.get_queryset()}
            for key in self.data:
                if key.startswith(formset.prefix+'-') and key.endswith('-id'):
                    value = self.data.get(key)
                    if value and str(value) not in allowed:
                        raise ValidationError('다른 콘텐츠에 속한 사진 배치나 약력을 수정할 수 없습니다.')
        return data
    def is_valid(self):
        valid = super().is_valid()
        if not valid:
            return False
        candidates = [(self, self.cleaned_data)]
        for formset in self.formsets.values():
            candidates.extend((form, form.cleaned_data) for form in formset.forms if not form.cleaned_data.get('DELETE'))
        for form, data in candidates:
            for name, value in list(data.items()):
                if hasattr(value, 'collection_id') and hasattr(value, 'file'):
                    if self.for_user is None or not permission_policy.user_has_any_permission_for_instance(self.for_user, ['choose','change'], value):
                        form.add_error(name, '선택 권한이 없는 이미지입니다.')
                        valid = False
        return valid

class AddressConfirmationWidget(forms.HiddenInput):
    template_name = 'content/widgets/address_confirmation.html'
    class Media:
        js = ['google-maps.js', 'branch-google-map.js']
        css = {'all': ['branch-address.css']}
    def get_context(self, name, value, attrs):
        context = super().get_context(name, '', attrs)
        context['saved_confirmed'] = self.attrs.get('data-saved-confirmed')
        return context

class BranchForm(ContentForm):
    google_map_input = forms.CharField(required=False, max_length=8192, label='Google 지도 퍼가기', widget=forms.Textarea(attrs={'rows': 4}), help_text='Google 지도에서 공유 → 지도 퍼가기 → HTML 복사한 코드를 붙여넣으세요. 해당 코드의 주소만 입력해도 됩니다. 비우고 저장하면 지도를 제거합니다. 주소 변경 시 새 지도를 등록·확인하세요.')
    map_confirmation_url = forms.CharField(required=False, max_length=4096, widget=forms.HiddenInput)
    map_confirmation = forms.BooleanField(required=False, label='지도 위치 확인', widget=AddressConfirmationWidget)
    map_confirmation_address = forms.CharField(required=False, max_length=255, widget=forms.HiddenInput)
    map_confirmation_version = forms.IntegerField(required=False, min_value=0, widget=forms.HiddenInput)

    replacement_main = forms.ModelChoiceField(queryset=None, required=False, label='비공개 전환 시 새 본점', help_text='현재 본점을 비공개로 바꿀 때 다른 공개 지점을 선택하세요. 같은 저장에서 함께 변경됩니다.')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Branch
        self.fields['map_confirmation'].widget.attrs.update({'data-saved-confirmed': 'true' if self.instance.google_map_confirmed else 'false', 'data-saved-address': self.instance.google_map_address, 'data-saved-url': self.instance.google_embed_url})
        self.fields['google_map_input'].initial = self.instance.google_embed_url
        self.fields['replacement_main'].queryset = Branch.objects.filter(is_public=True).exclude(pk=self.instance.pk)
    def clean(self):
        data = super().clean()
        from .google_maps import parse_embed_input
        self.instance._google_map_confirmation = None
        try:
            url = parse_embed_input(data.get('google_map_input', ''))
        except ValidationError as error:
            self.add_error('google_map_input', error)
            url = ''
        # The noneditable model field can only receive a validated URL, not HTML.
        self.instance.google_embed_url = url
        if data.get('map_confirmation'):
            action = 'change' if self.instance.pk else 'add'
            if self.for_user is None or not self.for_user.has_perm(f'content.{action}_branch'):
                raise ValidationError('지도 위치 확인 권한이 없습니다.')
            if (not url or not data.get('address') or data.get('map_confirmation_address') != data['address']
                    or data.get('map_confirmation_url') != url
                    or data.get('map_confirmation_version') != data.get('edit_version')):
                raise ValidationError('입력한 기본 주소와 지도의 위치를 다시 확인하세요.')
            self.instance._google_map_confirmation = (data['address'], url, data['edit_version'])
        replacement = data.get('replacement_main')
        self.instance._replacement_main_id = replacement.pk if replacement else None
        if not data.get('is_public') and replacement:
            data['is_main'] = False
        return data
