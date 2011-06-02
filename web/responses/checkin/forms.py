from django import forms
from django.utils import simplejson
from web.responses.checkin.models import *
from gmapsfield.fields import *

class CheckInResponseForm(forms.ModelForm):
    map = GoogleMapsField()
    comment = forms.CharField(max_length=1000,required=True)
    class Meta:
        model = CheckInResponse
        fields = ('map',)
    
    def clean(self):
        map = self.cleaned_data.get('map')
        if not map or not simplejson.loads(map).has_key('coordinates'):
          raise forms.ValidationError('Please make a selection on the map.')

        return self.cleaned_data
