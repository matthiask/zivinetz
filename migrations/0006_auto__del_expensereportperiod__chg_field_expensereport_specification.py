# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Deleting model 'ExpenseReportPeriod'
        db.delete_table(u'zivinetz_expensereportperiod')

        # Changing field 'ExpenseReport.specification'
        db.alter_column(u'zivinetz_expensereport', 'specification_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['zivinetz.Specification']))

    def backwards(self, orm):

        # Adding model 'ExpenseReportPeriod'
        db.create_table(u'zivinetz_expensereportperiod', (
            ('expense_report', self.gf('django.db.models.fields.related.ForeignKey')(related_name='periods', to=orm['zivinetz.ExpenseReport'])),
            ('date_from', self.gf('django.db.models.fields.DateField')()),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('specification', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zivinetz.Specification'])),
        ))
        db.send_create_signal(u'zivinetz', ['ExpenseReportPeriod'])

        # Changing field 'ExpenseReport.specification'
        db.alter_column(u'zivinetz_expensereport', 'specification_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zivinetz.Specification'], null=True))

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 11, 1, 9, 58, 16, 417248)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 11, 1, 9, 58, 16, 417114)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'zivinetz.assessment': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Assessment'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'drudge': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assessments'", 'to': u"orm['zivinetz.Drudge']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mark': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'zivinetz.assignment': {
            'Meta': {'ordering': "['-date_from', '-date_until']", 'object_name': 'Assignment'},
            'arranged_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_from': ('django.db.models.fields.DateField', [], {}),
            'date_until': ('django.db.models.fields.DateField', [], {}),
            'date_until_extension': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'drudge': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': u"orm['zivinetz.Drudge']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobilized_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'part_of_long_assignment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'regional_office': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zivinetz.RegionalOffice']"}),
            'specification': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zivinetz.Specification']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '10'})
        },
        u'zivinetz.codeword': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Codeword'},
            'codeword': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'})
        },
        u'zivinetz.companyholiday': {
            'Meta': {'ordering': "['date_from']", 'object_name': 'CompanyHoliday'},
            'date_from': ('django.db.models.fields.DateField', [], {}),
            'date_until': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'zivinetz.compensationset': {
            'Meta': {'ordering': "['-valid_from']", 'object_name': 'CompensationSet'},
            'accomodation_home': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'breakfast_at_accomodation': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'breakfast_external': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'clothing': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '6'}),
            'clothing_limit_per_assignment': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lunch_at_accomodation': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'lunch_external': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'private_transport_per_km': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'spending_money': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'supper_at_accomodation': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'supper_external': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'valid_from': ('django.db.models.fields.DateField', [], {'unique': 'True'})
        },
        u'zivinetz.drudge': {
            'Meta': {'ordering': "['user__last_name', 'user__first_name', 'zdp_no']", 'object_name': 'Drudge'},
            'address': ('django.db.models.fields.TextField', [], {}),
            'bank_account': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {}),
            'driving_license': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'education_occupation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'environment_course': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'general_abonnement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'half_fare_card': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'health_insurance_account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'health_insurance_company': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'motor_saw_course': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'other_card': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'phone_home': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'phone_office': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'place_of_citizenship_city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'place_of_citizenship_state': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'profile_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'regional_office': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zivinetz.RegionalOffice']"}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'vegetarianism': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'zdp_no': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'zivinetz.expensereport': {
            'Meta': {'ordering': "['assignment__drudge', 'date_from']", 'object_name': 'ExpenseReport'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': u"orm['zivinetz.Assignment']"}),
            'calculated_total_days': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'clothing_expenses': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '10', 'decimal_places': '2'}),
            'clothing_expenses_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'date_from': ('django.db.models.fields.DateField', [], {}),
            'date_until': ('django.db.models.fields.DateField', [], {}),
            'forced_leave_days': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'forced_leave_days_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'free_days': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'free_days_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'holi_days': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'holi_days_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'miscellaneous': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '10', 'decimal_places': '2'}),
            'miscellaneous_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'report_no': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'sick_days': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'sick_days_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'specification': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zivinetz.Specification']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '2'}),
            'transport_expenses': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '10', 'decimal_places': '2'}),
            'transport_expenses_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'working_days': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'working_days_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'zivinetz.jobreference': {
            'Meta': {'ordering': "['-created']", 'object_name': 'JobReference'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobreferences'", 'to': u"orm['zivinetz.Assignment']"}),
            'created': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'zivinetz.jobreferencetemplate': {
            'Meta': {'ordering': "['title']", 'object_name': 'JobReferenceTemplate'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'zivinetz.publicholiday': {
            'Meta': {'ordering': "['date']", 'object_name': 'PublicHoliday'},
            'date': ('django.db.models.fields.DateField', [], {'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'zivinetz.regionaloffice': {
            'Meta': {'ordering': "['name']", 'object_name': 'RegionalOffice'},
            'address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        },
        u'zivinetz.scopestatement': {
            'Meta': {'ordering': "['name']", 'object_name': 'ScopeStatement'},
            'eis_no': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'zivinetz.specification': {
            'Meta': {'ordering': "['scope_statement', 'with_accomodation']", 'unique_together': "(('scope_statement', 'with_accomodation'),)", 'object_name': 'Specification'},
            'accomodation_free': ('django.db.models.fields.CharField', [], {'default': "'provided'", 'max_length': '20'}),
            'accomodation_sick': ('django.db.models.fields.CharField', [], {'default': "'provided'", 'max_length': '20'}),
            'accomodation_throughout': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'accomodation_working': ('django.db.models.fields.CharField', [], {'default': "'provided'", 'max_length': '20'}),
            'breakfast_free': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'breakfast_sick': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'breakfast_working': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'clothing': ('django.db.models.fields.CharField', [], {'default': "'provided'", 'max_length': '20'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'conditions': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'food_throughout': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lunch_free': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'lunch_sick': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'lunch_working': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'scope_statement': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'specifications'", 'to': u"orm['zivinetz.ScopeStatement']"}),
            'supper_free': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'supper_sick': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'supper_working': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'with_accomodation': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'zivinetz.waitlist': {
            'Meta': {'ordering': "['created']", 'object_name': 'WaitList'},
            'assignment_date_from': ('django.db.models.fields.DateField', [], {}),
            'assignment_date_until': ('django.db.models.fields.DateField', [], {}),
            'assignment_duration': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'drudge': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zivinetz.Drudge']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'specification': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['zivinetz.Specification']"})
        }
    }

    complete_apps = ['zivinetz']
