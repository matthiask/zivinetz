# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ScopeStatement'
        db.create_table('zivinetz_scopestatement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('eis_no', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('zivinetz', ['ScopeStatement'])

        # Adding model 'Specification'
        db.create_table('zivinetz_specification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scope_statement', self.gf('django.db.models.fields.related.ForeignKey')(related_name='specifications', to=orm['zivinetz.ScopeStatement'])),
            ('with_accomodation', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('accomodation_working', self.gf('django.db.models.fields.CharField')(default='provided', max_length=20)),
            ('breakfast_working', self.gf('django.db.models.fields.CharField')(default='no_compensation', max_length=20)),
            ('lunch_working', self.gf('django.db.models.fields.CharField')(default='no_compensation', max_length=20)),
            ('supper_working', self.gf('django.db.models.fields.CharField')(default='no_compensation', max_length=20)),
            ('accomodation_sick', self.gf('django.db.models.fields.CharField')(default='provided', max_length=20)),
            ('breakfast_sick', self.gf('django.db.models.fields.CharField')(default='no_compensation', max_length=20)),
            ('lunch_sick', self.gf('django.db.models.fields.CharField')(default='no_compensation', max_length=20)),
            ('supper_sick', self.gf('django.db.models.fields.CharField')(default='no_compensation', max_length=20)),
            ('accomodation_free', self.gf('django.db.models.fields.CharField')(default='provided', max_length=20)),
            ('breakfast_free', self.gf('django.db.models.fields.CharField')(default='no_compensation', max_length=20)),
            ('lunch_free', self.gf('django.db.models.fields.CharField')(default='no_compensation', max_length=20)),
            ('supper_free', self.gf('django.db.models.fields.CharField')(default='no_compensation', max_length=20)),
            ('clothing', self.gf('django.db.models.fields.CharField')(default='provided', max_length=20)),
            ('accomodation_throughout', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('food_throughout', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('conditions', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('zivinetz', ['Specification'])

        # Adding unique constraint on 'Specification', fields ['scope_statement', 'with_accomodation']
        db.create_unique('zivinetz_specification', ['scope_statement_id', 'with_accomodation'])

        # Adding model 'CompensationSet'
        db.create_table('zivinetz_compensationset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('valid_from', self.gf('django.db.models.fields.DateField')(unique=True)),
            ('spending_money', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('breakfast_at_accomodation', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('lunch_at_accomodation', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('supper_at_accomodation', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('breakfast_external', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('lunch_external', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('supper_external', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('accomodation_home', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('private_transport_per_km', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('clothing', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=6)),
            ('clothing_limit_per_assignment', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal('zivinetz', ['CompensationSet'])

        # Adding model 'RegionalOffice'
        db.create_table('zivinetz_regionaloffice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('address', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('fax', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
        ))
        db.send_create_signal('zivinetz', ['RegionalOffice'])

        # Adding model 'Drudge'
        db.create_table('zivinetz_drudge', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('zdp_no', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
            ('address', self.gf('django.db.models.fields.TextField')()),
            ('zip_code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('date_of_birth', self.gf('django.db.models.fields.DateField')()),
            ('place_of_citizenship_city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('place_of_citizenship_state', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('phone_home', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('phone_office', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('mobile', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('bank_account', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('health_insurance_company', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('health_insurance_account', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('education_occupation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('driving_license', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('general_abonnement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('half_fare_card', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('other_card', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('vegetarianism', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('environment_course', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('motor_saw_course', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('regional_office', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zivinetz.RegionalOffice'])),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('zivinetz', ['Drudge'])

        # Adding model 'Assignment'
        db.create_table('zivinetz_assignment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('specification', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zivinetz.Specification'])),
            ('drudge', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignments', to=orm['zivinetz.Drudge'])),
            ('regional_office', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zivinetz.RegionalOffice'])),
            ('date_from', self.gf('django.db.models.fields.DateField')()),
            ('date_until', self.gf('django.db.models.fields.DateField')()),
            ('date_until_extension', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('part_of_long_assignment', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('arranged_on', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('mobilized_on', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('zivinetz', ['Assignment'])

        # Adding model 'ExpenseReport'
        db.create_table('zivinetz_expensereport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('assignment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reports', to=orm['zivinetz.Assignment'])),
            ('date_from', self.gf('django.db.models.fields.DateField')()),
            ('date_until', self.gf('django.db.models.fields.DateField')()),
            ('report_no', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=10)),
            ('working_days', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('working_days_notes', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('free_days', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('free_days_notes', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('sick_days', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('sick_days_notes', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('holi_days', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('holi_days_notes', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('forced_leave_days', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('forced_leave_days_notes', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('clothing_expenses', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=10, decimal_places=2)),
            ('clothing_expenses_notes', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('transport_expenses', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=10, decimal_places=2)),
            ('transport_expenses_notes', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('miscellaneous', self.gf('django.db.models.fields.DecimalField')(default='0.00', max_digits=10, decimal_places=2)),
            ('miscellaneous_notes', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('total', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal('zivinetz', ['ExpenseReport'])

        # Adding model 'ExpenseReportPeriod'
        db.create_table('zivinetz_expensereportperiod', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('expense_report', self.gf('django.db.models.fields.related.ForeignKey')(related_name='periods', to=orm['zivinetz.ExpenseReport'])),
            ('specification', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zivinetz.Specification'])),
            ('date_from', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('zivinetz', ['ExpenseReportPeriod'])

        # Adding model 'PublicHoliday'
        db.create_table('zivinetz_publicholiday', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('date', self.gf('django.db.models.fields.DateField')(unique=True)),
        ))
        db.send_create_signal('zivinetz', ['PublicHoliday'])

        # Adding model 'CompanyHoliday'
        db.create_table('zivinetz_companyholiday', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_from', self.gf('django.db.models.fields.DateField')()),
            ('date_until', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('zivinetz', ['CompanyHoliday'])

        # Adding model 'WaitList'
        db.create_table('zivinetz_waitlist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('drudge', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zivinetz.Drudge'])),
            ('specification', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['zivinetz.Specification'])),
            ('assignment_date_from', self.gf('django.db.models.fields.DateField')()),
            ('assignment_date_until', self.gf('django.db.models.fields.DateField')()),
            ('assignment_duration', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('zivinetz', ['WaitList'])

        # Adding model 'Assessment'
        db.create_table('zivinetz_assessment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('drudge', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assessments', to=orm['zivinetz.Drudge'])),
            ('mark', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('zivinetz', ['Assessment'])

        # Adding model 'Codeword'
        db.create_table('zivinetz_codeword', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=10, db_index=True)),
            ('codeword', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('zivinetz', ['Codeword'])

        # Adding model 'JobReferenceTemplate'
        db.create_table('zivinetz_jobreferencetemplate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('zivinetz', ['JobReferenceTemplate'])

        # Adding model 'JobReference'
        db.create_table('zivinetz_jobreference', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('assignment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobreferences', to=orm['zivinetz.Assignment'])),
            ('created', self.gf('django.db.models.fields.DateField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('zivinetz', ['JobReference'])

    def backwards(self, orm):
        
        # Removing unique constraint on 'Specification', fields ['scope_statement', 'with_accomodation']
        db.delete_unique('zivinetz_specification', ['scope_statement_id', 'with_accomodation'])

        # Deleting model 'ScopeStatement'
        db.delete_table('zivinetz_scopestatement')

        # Deleting model 'Specification'
        db.delete_table('zivinetz_specification')

        # Deleting model 'CompensationSet'
        db.delete_table('zivinetz_compensationset')

        # Deleting model 'RegionalOffice'
        db.delete_table('zivinetz_regionaloffice')

        # Deleting model 'Drudge'
        db.delete_table('zivinetz_drudge')

        # Deleting model 'Assignment'
        db.delete_table('zivinetz_assignment')

        # Deleting model 'ExpenseReport'
        db.delete_table('zivinetz_expensereport')

        # Deleting model 'ExpenseReportPeriod'
        db.delete_table('zivinetz_expensereportperiod')

        # Deleting model 'PublicHoliday'
        db.delete_table('zivinetz_publicholiday')

        # Deleting model 'CompanyHoliday'
        db.delete_table('zivinetz_companyholiday')

        # Deleting model 'WaitList'
        db.delete_table('zivinetz_waitlist')

        # Deleting model 'Assessment'
        db.delete_table('zivinetz_assessment')

        # Deleting model 'Codeword'
        db.delete_table('zivinetz_codeword')

        # Deleting model 'JobReferenceTemplate'
        db.delete_table('zivinetz_jobreferencetemplate')

        # Deleting model 'JobReference'
        db.delete_table('zivinetz_jobreference')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 10, 8, 29, 52, 135016)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 4, 10, 8, 29, 52, 134901)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'zivinetz.assessment': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Assessment'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'drudge': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assessments'", 'to': "orm['zivinetz.Drudge']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mark': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'zivinetz.assignment': {
            'Meta': {'ordering': "['-date_from', '-date_until']", 'object_name': 'Assignment'},
            'arranged_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_from': ('django.db.models.fields.DateField', [], {}),
            'date_until': ('django.db.models.fields.DateField', [], {}),
            'date_until_extension': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'drudge': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': "orm['zivinetz.Drudge']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobilized_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'part_of_long_assignment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'regional_office': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zivinetz.RegionalOffice']"}),
            'specification': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zivinetz.Specification']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '10'})
        },
        'zivinetz.codeword': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Codeword'},
            'codeword': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'})
        },
        'zivinetz.companyholiday': {
            'Meta': {'ordering': "['date_from']", 'object_name': 'CompanyHoliday'},
            'date_from': ('django.db.models.fields.DateField', [], {}),
            'date_until': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'zivinetz.compensationset': {
            'Meta': {'ordering': "['-valid_from']", 'object_name': 'CompensationSet'},
            'accomodation_home': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'breakfast_at_accomodation': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'breakfast_external': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'clothing': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '6'}),
            'clothing_limit_per_assignment': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lunch_at_accomodation': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'lunch_external': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'private_transport_per_km': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'spending_money': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'supper_at_accomodation': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'supper_external': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'valid_from': ('django.db.models.fields.DateField', [], {'unique': 'True'})
        },
        'zivinetz.drudge': {
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'motor_saw_course': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'other_card': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'phone_home': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'phone_office': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'place_of_citizenship_city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'place_of_citizenship_state': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'regional_office': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zivinetz.RegionalOffice']"}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'vegetarianism': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'zdp_no': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'zivinetz.expensereport': {
            'Meta': {'ordering': "['assignment__drudge', 'date_from']", 'object_name': 'ExpenseReport'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': "orm['zivinetz.Assignment']"}),
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'miscellaneous': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '10', 'decimal_places': '2'}),
            'miscellaneous_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'report_no': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'sick_days': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'sick_days_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '2'}),
            'transport_expenses': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '10', 'decimal_places': '2'}),
            'transport_expenses_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'working_days': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'working_days_notes': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'zivinetz.expensereportperiod': {
            'Meta': {'ordering': "['date_from']", 'object_name': 'ExpenseReportPeriod'},
            'date_from': ('django.db.models.fields.DateField', [], {}),
            'expense_report': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'periods'", 'to': "orm['zivinetz.ExpenseReport']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'specification': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zivinetz.Specification']"})
        },
        'zivinetz.jobreference': {
            'Meta': {'object_name': 'JobReference'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobreferences'", 'to': "orm['zivinetz.Assignment']"}),
            'created': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'zivinetz.jobreferencetemplate': {
            'Meta': {'ordering': "['title']", 'object_name': 'JobReferenceTemplate'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'zivinetz.publicholiday': {
            'Meta': {'ordering': "['date']", 'object_name': 'PublicHoliday'},
            'date': ('django.db.models.fields.DateField', [], {'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'zivinetz.regionaloffice': {
            'Meta': {'ordering': "['name']", 'object_name': 'RegionalOffice'},
            'address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        },
        'zivinetz.scopestatement': {
            'Meta': {'ordering': "['name']", 'object_name': 'ScopeStatement'},
            'eis_no': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'zivinetz.specification': {
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lunch_free': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'lunch_sick': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'lunch_working': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'scope_statement': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'specifications'", 'to': "orm['zivinetz.ScopeStatement']"}),
            'supper_free': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'supper_sick': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'supper_working': ('django.db.models.fields.CharField', [], {'default': "'no_compensation'", 'max_length': '20'}),
            'with_accomodation': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'zivinetz.waitlist': {
            'Meta': {'ordering': "['created']", 'object_name': 'WaitList'},
            'assignment_date_from': ('django.db.models.fields.DateField', [], {}),
            'assignment_date_until': ('django.db.models.fields.DateField', [], {}),
            'assignment_duration': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'drudge': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zivinetz.Drudge']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'specification': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['zivinetz.Specification']"})
        }
    }

    complete_apps = ['zivinetz']
