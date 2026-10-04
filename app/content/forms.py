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
                        raise ValidationError('다른 지점의 시설 사진 배치를 수정할 수 없습니다.')
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

class BranchForm(ContentForm):
    replacement_main = forms.ModelChoiceField(queryset=None, required=False, label='비공개 전환 시 새 본점', help_text='현재 본점을 비공개로 바꿀 때 다른 공개 지점을 선택하세요. 같은 저장에서 함께 변경됩니다.')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Branch
        self.fields['replacement_main'].queryset = Branch.objects.filter(is_public=True).exclude(pk=self.instance.pk)
    def clean(self):
        data = super().clean()
        replacement = data.get('replacement_main')
        self.instance._replacement_main_id = replacement.pk if replacement else None
        if not data.get('is_public') and replacement:
            data['is_main'] = False
        return data
