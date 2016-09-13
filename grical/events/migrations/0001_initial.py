# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import django.contrib.auth.models
import grical.events.utils
import django.contrib.gis.db.models.fields
from django.conf import settings
import re
import grical.tagging.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reversion', '0001_squashed_0004_auto_20160611_1202'),
    ]

    operations = [
        migrations.CreateModel(
            name='Calendar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_added', models.DateField(auto_now_add=True, verbose_name='Date added')),
            ],
            options={
                'verbose_name': 'Calendar',
                'verbose_name_plural': 'Calendars',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_time', models.DateTimeField(auto_now_add=True, verbose_name='Creation time')),
                ('modification_time', models.DateTimeField(auto_now=True, verbose_name='Modification time')),
                ('version', models.PositiveSmallIntegerField(default=1, verbose_name='version', editable=False)),
                ('acronym', models.CharField(help_text='Example: 26C3', max_length=20, null=True, verbose_name='Acronym', blank=True)),
                ('title', models.CharField(max_length=200, verbose_name='Title')),
                ('starttime', models.TimeField(help_text='Example: 18:00', null=True, verbose_name='Start time', blank=True)),
                ('endtime', models.TimeField(help_text='Example: 19:00', null=True, verbose_name='End time', blank=True)),
                ('timezone', models.CharField(blank=True, max_length=30, null=True, verbose_name='Timezone', choices=[('Africa', ((b'Africa/Abidjan', 'Africa/Abidjan'), (b'Africa/Accra', 'Africa/Accra'), (b'Africa/Addis_Ababa', 'Africa/Addis Ababa'), (b'Africa/Algiers', 'Africa/Algiers'), (b'Africa/Asmara', 'Africa/Asmara'), (b'Africa/Bamako', 'Africa/Bamako'), (b'Africa/Bangui', 'Africa/Bangui'), (b'Africa/Banjul', 'Africa/Banjul'), (b'Africa/Bissau', 'Africa/Bissau'), (b'Africa/Blantyre', 'Africa/Blantyre'), (b'Africa/Brazzaville', 'Africa/Brazzaville'), (b'Africa/Bujumbura', 'Africa/Bujumbura'), (b'Africa/Cairo', 'Africa/Cairo'), (b'Africa/Casablanca', 'Africa/Casablanca'), (b'Africa/Ceuta', 'Africa/Ceuta'), (b'Africa/Conakry', 'Africa/Conakry'), (b'Africa/Dakar', 'Africa/Dakar'), (b'Africa/Dar_es_Salaam', 'Africa/Dar es Salaam'), (b'Africa/Djibouti', 'Africa/Djibouti'), (b'Africa/Douala', 'Africa/Douala'), (b'Africa/El_Aaiun', 'Africa/El Aaiun'), (b'Africa/Freetown', 'Africa/Freetown'), (b'Africa/Gaborone', 'Africa/Gaborone'), (b'Africa/Harare', 'Africa/Harare'), (b'Africa/Johannesburg', 'Africa/Johannesburg'), (b'Africa/Kampala', 'Africa/Kampala'), (b'Africa/Khartoum', 'Africa/Khartoum'), (b'Africa/Kigali', 'Africa/Kigali'), (b'Africa/Kinshasa', 'Africa/Kinshasa'), (b'Africa/Lagos', 'Africa/Lagos'), (b'Africa/Libreville', 'Africa/Libreville'), (b'Africa/Lome', 'Africa/Lome'), (b'Africa/Luanda', 'Africa/Luanda'), (b'Africa/Lubumbashi', 'Africa/Lubumbashi'), (b'Africa/Lusaka', 'Africa/Lusaka'), (b'Africa/Malabo', 'Africa/Malabo'), (b'Africa/Maputo', 'Africa/Maputo'), (b'Africa/Maseru', 'Africa/Maseru'), (b'Africa/Mbabane', 'Africa/Mbabane'), (b'Africa/Mogadishu', 'Africa/Mogadishu'), (b'Africa/Monrovia', 'Africa/Monrovia'), (b'Africa/Nairobi', 'Africa/Nairobi'), (b'Africa/Ndjamena', 'Africa/Ndjamena'), (b'Africa/Niamey', 'Africa/Niamey'), (b'Africa/Nouakchott', 'Africa/Nouakchott'), (b'Africa/Ouagadougou', 'Africa/Ouagadougou'), (b'Africa/Porto-Novo', 'Africa/Porto-Novo'), (b'Africa/Sao_Tome', 'Africa/Sao Tome'), (b'Africa/Tripoli', 'Africa/Tripoli'), (b'Africa/Tunis', 'Africa/Tunis'), (b'Africa/Windhoek', 'Africa/Windhoek'))), ('America', ((b'America/Adak', 'America/Adak'), (b'America/Anchorage', 'America/Anchorage'), (b'America/Anguilla', 'America/Anguilla'), (b'America/Antigua', 'America/Antigua'), (b'America/Araguaina', 'America/Araguaina'), (b'America/Argentina/Buenos_Aires', 'America/Argentina/Buenos Aires'), (b'America/Argentina/Catamarca', 'America/Argentina/Catamarca'), (b'America/Argentina/Cordoba', 'America/Argentina/Cordoba'), (b'America/Argentina/Jujuy', 'America/Argentina/Jujuy'), (b'America/Argentina/La_Rioja', 'America/Argentina/La Rioja'), (b'America/Argentina/Mendoza', 'America/Argentina/Mendoza'), (b'America/Argentina/Rio_Gallegos', 'America/Argentina/Rio Gallegos'), (b'America/Argentina/Salta', 'America/Argentina/Salta'), (b'America/Argentina/San_Juan', 'America/Argentina/San Juan'), (b'America/Argentina/San_Luis', 'America/Argentina/San Luis'), (b'America/Argentina/Tucuman', 'America/Argentina/Tucuman'), (b'America/Argentina/Ushuaia', 'America/Argentina/Ushuaia'), (b'America/Aruba', 'America/Aruba'), (b'America/Asuncion', 'America/Asuncion'), (b'America/Atikokan', 'America/Atikokan'), (b'America/Bahia', 'America/Bahia'), (b'America/Barbados', 'America/Barbados'), (b'America/Belem', 'America/Belem'), (b'America/Belize', 'America/Belize'), (b'America/Blanc-Sablon', 'America/Blanc-Sablon'), (b'America/Boa_Vista', 'America/Boa Vista'), (b'America/Bogota', 'America/Bogota'), (b'America/Boise', 'America/Boise'), (b'America/Cambridge_Bay', 'America/Cambridge Bay'), (b'America/Campo_Grande', 'America/Campo Grande'), (b'America/Cancun', 'America/Cancun'), (b'America/Caracas', 'America/Caracas'), (b'America/Cayenne', 'America/Cayenne'), (b'America/Cayman', 'America/Cayman'), (b'America/Chicago', 'America/Chicago'), (b'America/Chihuahua', 'America/Chihuahua'), (b'America/Costa_Rica', 'America/Costa Rica'), (b'America/Cuiaba', 'America/Cuiaba'), (b'America/Curacao', 'America/Curacao'), (b'America/Danmarkshavn', 'America/Danmarkshavn'), (b'America/Dawson', 'America/Dawson'), (b'America/Dawson_Creek', 'America/Dawson Creek'), (b'America/Denver', 'America/Denver'), (b'America/Detroit', 'America/Detroit'), (b'America/Dominica', 'America/Dominica'), (b'America/Edmonton', 'America/Edmonton'), (b'America/Eirunepe', 'America/Eirunepe'), (b'America/El_Salvador', 'America/El Salvador'), (b'America/Fortaleza', 'America/Fortaleza'), (b'America/Glace_Bay', 'America/Glace Bay'), (b'America/Godthab', 'America/Godthab'), (b'America/Goose_Bay', 'America/Goose Bay'), (b'America/Grand_Turk', 'America/Grand Turk'), (b'America/Grenada', 'America/Grenada'), (b'America/Guadeloupe', 'America/Guadeloupe'), (b'America/Guatemala', 'America/Guatemala'), (b'America/Guayaquil', 'America/Guayaquil'), (b'America/Guyana', 'America/Guyana'), (b'America/Halifax', 'America/Halifax'), (b'America/Havana', 'America/Havana'), (b'America/Hermosillo', 'America/Hermosillo'), (b'America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), (b'America/Indiana/Knox', 'America/Indiana/Knox'), (b'America/Indiana/Marengo', 'America/Indiana/Marengo'), (b'America/Indiana/Petersburg', 'America/Indiana/Petersburg'), (b'America/Indiana/Tell_City', 'America/Indiana/Tell City'), (b'America/Indiana/Vevay', 'America/Indiana/Vevay'), (b'America/Indiana/Vincennes', 'America/Indiana/Vincennes'), (b'America/Indiana/Winamac', 'America/Indiana/Winamac'), (b'America/Inuvik', 'America/Inuvik'), (b'America/Iqaluit', 'America/Iqaluit'), (b'America/Jamaica', 'America/Jamaica'), (b'America/Juneau', 'America/Juneau'), (b'America/Kentucky/Louisville', 'America/Kentucky/Louisville'), (b'America/Kentucky/Monticello', 'America/Kentucky/Monticello'), (b'America/La_Paz', 'America/La Paz'), (b'America/Lima', 'America/Lima'), (b'America/Los_Angeles', 'America/Los Angeles'), (b'America/Maceio', 'America/Maceio'), (b'America/Managua', 'America/Managua'), (b'America/Manaus', 'America/Manaus'), (b'America/Martinique', 'America/Martinique'), (b'America/Matamoros', 'America/Matamoros'), (b'America/Mazatlan', 'America/Mazatlan'), (b'America/Menominee', 'America/Menominee'), (b'America/Merida', 'America/Merida'), (b'America/Mexico_City', 'America/Mexico City'), (b'America/Miquelon', 'America/Miquelon'), (b'America/Moncton', 'America/Moncton'), (b'America/Monterrey', 'America/Monterrey'), (b'America/Montevideo', 'America/Montevideo'), (b'America/Montreal', 'America/Montreal'), (b'America/Montserrat', 'America/Montserrat'), (b'America/Nassau', 'America/Nassau'), (b'America/New_York', 'America/New York'), (b'America/Nipigon', 'America/Nipigon'), (b'America/Nome', 'America/Nome'), (b'America/Noronha', 'America/Noronha'), (b'America/North_Dakota/Center', 'America/North Dakota/Center'), (b'America/North_Dakota/New_Salem', 'America/North Dakota/New Salem'), (b'America/Ojinaga', 'America/Ojinaga'), (b'America/Panama', 'America/Panama'), (b'America/Pangnirtung', 'America/Pangnirtung'), (b'America/Paramaribo', 'America/Paramaribo'), (b'America/Phoenix', 'America/Phoenix'), (b'America/Port-au-Prince', 'America/Port-au-Prince'), (b'America/Port_of_Spain', 'America/Port of Spain'), (b'America/Porto_Velho', 'America/Porto Velho'), (b'America/Puerto_Rico', 'America/Puerto Rico'), (b'America/Rainy_River', 'America/Rainy River'), (b'America/Rankin_Inlet', 'America/Rankin Inlet'), (b'America/Recife', 'America/Recife'), (b'America/Regina', 'America/Regina'), (b'America/Resolute', 'America/Resolute'), (b'America/Rio_Branco', 'America/Rio Branco'), (b'America/Santa_Isabel', 'America/Santa Isabel'), (b'America/Santarem', 'America/Santarem'), (b'America/Santiago', 'America/Santiago'), (b'America/Santo_Domingo', 'America/Santo Domingo'), (b'America/Sao_Paulo', 'America/Sao Paulo'), (b'America/Scoresbysund', 'America/Scoresbysund'), (b'America/St_Johns', 'America/St Johns'), (b'America/St_Kitts', 'America/St Kitts'), (b'America/St_Lucia', 'America/St Lucia'), (b'America/St_Thomas', 'America/St Thomas'), (b'America/St_Vincent', 'America/St Vincent'), (b'America/Swift_Current', 'America/Swift Current'), (b'America/Tegucigalpa', 'America/Tegucigalpa'), (b'America/Thule', 'America/Thule'), (b'America/Thunder_Bay', 'America/Thunder Bay'), (b'America/Tijuana', 'America/Tijuana'), (b'America/Toronto', 'America/Toronto'), (b'America/Tortola', 'America/Tortola'), (b'America/Vancouver', 'America/Vancouver'), (b'America/Whitehorse', 'America/Whitehorse'), (b'America/Winnipeg', 'America/Winnipeg'), (b'America/Yakutat', 'America/Yakutat'), (b'America/Yellowknife', 'America/Yellowknife'))), ('Antarctica', ((b'Antarctica/Casey', 'Antarctica/Casey'), (b'Antarctica/Davis', 'Antarctica/Davis'), (b'Antarctica/DumontDUrville', 'Antarctica/DumontDUrville'), (b'Antarctica/Mawson', 'Antarctica/Mawson'), (b'Antarctica/McMurdo', 'Antarctica/McMurdo'), (b'Antarctica/Palmer', 'Antarctica/Palmer'), (b'Antarctica/Rothera', 'Antarctica/Rothera'), (b'Antarctica/Syowa', 'Antarctica/Syowa'), (b'Antarctica/Vostok', 'Antarctica/Vostok'))), ('Asia', ((b'Asia/Aden', 'Asia/Aden'), (b'Asia/Almaty', 'Asia/Almaty'), (b'Asia/Amman', 'Asia/Amman'), (b'Asia/Anadyr', 'Asia/Anadyr'), (b'Asia/Aqtau', 'Asia/Aqtau'), (b'Asia/Aqtobe', 'Asia/Aqtobe'), (b'Asia/Ashgabat', 'Asia/Ashgabat'), (b'Asia/Baghdad', 'Asia/Baghdad'), (b'Asia/Bahrain', 'Asia/Bahrain'), (b'Asia/Baku', 'Asia/Baku'), (b'Asia/Bangkok', 'Asia/Bangkok'), (b'Asia/Beirut', 'Asia/Beirut'), (b'Asia/Bishkek', 'Asia/Bishkek'), (b'Asia/Brunei', 'Asia/Brunei'), (b'Asia/Choibalsan', 'Asia/Choibalsan'), (b'Asia/Chongqing', 'Asia/Chongqing'), (b'Asia/Colombo', 'Asia/Colombo'), (b'Asia/Damascus', 'Asia/Damascus'), (b'Asia/Dhaka', 'Asia/Dhaka'), (b'Asia/Dili', 'Asia/Dili'), (b'Asia/Dubai', 'Asia/Dubai'), (b'Asia/Dushanbe', 'Asia/Dushanbe'), (b'Asia/Gaza', 'Asia/Gaza'), (b'Asia/Harbin', 'Asia/Harbin'), (b'Asia/Ho_Chi_Minh', 'Asia/Ho Chi Minh'), (b'Asia/Hong_Kong', 'Asia/Hong Kong'), (b'Asia/Hovd', 'Asia/Hovd'), (b'Asia/Irkutsk', 'Asia/Irkutsk'), (b'Asia/Jakarta', 'Asia/Jakarta'), (b'Asia/Jayapura', 'Asia/Jayapura'), (b'Asia/Jerusalem', 'Asia/Jerusalem'), (b'Asia/Kabul', 'Asia/Kabul'), (b'Asia/Kamchatka', 'Asia/Kamchatka'), (b'Asia/Karachi', 'Asia/Karachi'), (b'Asia/Kashgar', 'Asia/Kashgar'), (b'Asia/Kathmandu', 'Asia/Kathmandu'), (b'Asia/Kolkata', 'Asia/Kolkata'), (b'Asia/Krasnoyarsk', 'Asia/Krasnoyarsk'), (b'Asia/Kuala_Lumpur', 'Asia/Kuala Lumpur'), (b'Asia/Kuching', 'Asia/Kuching'), (b'Asia/Kuwait', 'Asia/Kuwait'), (b'Asia/Macau', 'Asia/Macau'), (b'Asia/Magadan', 'Asia/Magadan'), (b'Asia/Makassar', 'Asia/Makassar'), (b'Asia/Manila', 'Asia/Manila'), (b'Asia/Muscat', 'Asia/Muscat'), (b'Asia/Nicosia', 'Asia/Nicosia'), (b'Asia/Novokuznetsk', 'Asia/Novokuznetsk'), (b'Asia/Novosibirsk', 'Asia/Novosibirsk'), (b'Asia/Omsk', 'Asia/Omsk'), (b'Asia/Oral', 'Asia/Oral'), (b'Asia/Phnom_Penh', 'Asia/Phnom Penh'), (b'Asia/Pontianak', 'Asia/Pontianak'), (b'Asia/Pyongyang', 'Asia/Pyongyang'), (b'Asia/Qatar', 'Asia/Qatar'), (b'Asia/Qyzylorda', 'Asia/Qyzylorda'), (b'Asia/Rangoon', 'Asia/Rangoon'), (b'Asia/Riyadh', 'Asia/Riyadh'), (b'Asia/Sakhalin', 'Asia/Sakhalin'), (b'Asia/Samarkand', 'Asia/Samarkand'), (b'Asia/Seoul', 'Asia/Seoul'), (b'Asia/Shanghai', 'Asia/Shanghai'), (b'Asia/Singapore', 'Asia/Singapore'), (b'Asia/Taipei', 'Asia/Taipei'), (b'Asia/Tashkent', 'Asia/Tashkent'), (b'Asia/Tbilisi', 'Asia/Tbilisi'), (b'Asia/Tehran', 'Asia/Tehran'), (b'Asia/Thimphu', 'Asia/Thimphu'), (b'Asia/Tokyo', 'Asia/Tokyo'), (b'Asia/Ulaanbaatar', 'Asia/Ulaanbaatar'), (b'Asia/Urumqi', 'Asia/Urumqi'), (b'Asia/Vientiane', 'Asia/Vientiane'), (b'Asia/Vladivostok', 'Asia/Vladivostok'), (b'Asia/Yakutsk', 'Asia/Yakutsk'), (b'Asia/Yekaterinburg', 'Asia/Yekaterinburg'), (b'Asia/Yerevan', 'Asia/Yerevan'))), ('Atlantic', ((b'Atlantic/Azores', 'Atlantic/Azores'), (b'Atlantic/Bermuda', 'Atlantic/Bermuda'), (b'Atlantic/Canary', 'Atlantic/Canary'), (b'Atlantic/Cape_Verde', 'Atlantic/Cape Verde'), (b'Atlantic/Faroe', 'Atlantic/Faroe'), (b'Atlantic/Madeira', 'Atlantic/Madeira'), (b'Atlantic/Reykjavik', 'Atlantic/Reykjavik'), (b'Atlantic/South_Georgia', 'Atlantic/South Georgia'), (b'Atlantic/St_Helena', 'Atlantic/St Helena'), (b'Atlantic/Stanley', 'Atlantic/Stanley'))), ('Australia', ((b'Australia/Adelaide', 'Australia/Adelaide'), (b'Australia/Brisbane', 'Australia/Brisbane'), (b'Australia/Broken_Hill', 'Australia/Broken Hill'), (b'Australia/Currie', 'Australia/Currie'), (b'Australia/Darwin', 'Australia/Darwin'), (b'Australia/Eucla', 'Australia/Eucla'), (b'Australia/Hobart', 'Australia/Hobart'), (b'Australia/Lindeman', 'Australia/Lindeman'), (b'Australia/Lord_Howe', 'Australia/Lord Howe'), (b'Australia/Melbourne', 'Australia/Melbourne'), (b'Australia/Perth', 'Australia/Perth'), (b'Australia/Sydney', 'Australia/Sydney'))), ('Canada', ((b'Canada/Atlantic', 'Canada/Atlantic'), (b'Canada/Central', 'Canada/Central'), (b'Canada/Eastern', 'Canada/Eastern'), (b'Canada/Mountain', 'Canada/Mountain'), (b'Canada/Newfoundland', 'Canada/Newfoundland'), (b'Canada/Pacific', 'Canada/Pacific'))), ('Europe', ((b'Europe/Amsterdam', 'Europe/Amsterdam'), (b'Europe/Andorra', 'Europe/Andorra'), (b'Europe/Athens', 'Europe/Athens'), (b'Europe/Belgrade', 'Europe/Belgrade'), (b'Europe/Berlin', 'Europe/Berlin'), (b'Europe/Brussels', 'Europe/Brussels'), (b'Europe/Bucharest', 'Europe/Bucharest'), (b'Europe/Budapest', 'Europe/Budapest'), (b'Europe/Chisinau', 'Europe/Chisinau'), (b'Europe/Copenhagen', 'Europe/Copenhagen'), (b'Europe/Dublin', 'Europe/Dublin'), (b'Europe/Gibraltar', 'Europe/Gibraltar'), (b'Europe/Helsinki', 'Europe/Helsinki'), (b'Europe/Istanbul', 'Europe/Istanbul'), (b'Europe/Kaliningrad', 'Europe/Kaliningrad'), (b'Europe/Kiev', 'Europe/Kiev'), (b'Europe/Lisbon', 'Europe/Lisbon'), (b'Europe/London', 'Europe/London'), (b'Europe/Luxembourg', 'Europe/Luxembourg'), (b'Europe/Madrid', 'Europe/Madrid'), (b'Europe/Malta', 'Europe/Malta'), (b'Europe/Minsk', 'Europe/Minsk'), (b'Europe/Monaco', 'Europe/Monaco'), (b'Europe/Moscow', 'Europe/Moscow'), (b'Europe/Oslo', 'Europe/Oslo'), (b'Europe/Paris', 'Europe/Paris'), (b'Europe/Prague', 'Europe/Prague'), (b'Europe/Riga', 'Europe/Riga'), (b'Europe/Rome', 'Europe/Rome'), (b'Europe/Samara', 'Europe/Samara'), (b'Europe/Simferopol', 'Europe/Simferopol'), (b'Europe/Sofia', 'Europe/Sofia'), (b'Europe/Stockholm', 'Europe/Stockholm'), (b'Europe/Tallinn', 'Europe/Tallinn'), (b'Europe/Tirane', 'Europe/Tirane'), (b'Europe/Uzhgorod', 'Europe/Uzhgorod'), (b'Europe/Vaduz', 'Europe/Vaduz'), (b'Europe/Vienna', 'Europe/Vienna'), (b'Europe/Vilnius', 'Europe/Vilnius'), (b'Europe/Volgograd', 'Europe/Volgograd'), (b'Europe/Warsaw', 'Europe/Warsaw'), (b'Europe/Zaporozhye', 'Europe/Zaporozhye'), (b'Europe/Zurich', 'Europe/Zurich'))), ('GMT', ((b'GMT', 'GMT'),)), ('Indian', ((b'Indian/Antananarivo', 'Indian/Antananarivo'), (b'Indian/Chagos', 'Indian/Chagos'), (b'Indian/Christmas', 'Indian/Christmas'), (b'Indian/Cocos', 'Indian/Cocos'), (b'Indian/Comoro', 'Indian/Comoro'), (b'Indian/Kerguelen', 'Indian/Kerguelen'), (b'Indian/Mahe', 'Indian/Mahe'), (b'Indian/Maldives', 'Indian/Maldives'), (b'Indian/Mauritius', 'Indian/Mauritius'), (b'Indian/Mayotte', 'Indian/Mayotte'), (b'Indian/Reunion', 'Indian/Reunion'))), ('Pacific', ((b'Pacific/Apia', 'Pacific/Apia'), (b'Pacific/Auckland', 'Pacific/Auckland'), (b'Pacific/Chatham', 'Pacific/Chatham'), (b'Pacific/Easter', 'Pacific/Easter'), (b'Pacific/Efate', 'Pacific/Efate'), (b'Pacific/Enderbury', 'Pacific/Enderbury'), (b'Pacific/Fakaofo', 'Pacific/Fakaofo'), (b'Pacific/Fiji', 'Pacific/Fiji'), (b'Pacific/Funafuti', 'Pacific/Funafuti'), (b'Pacific/Galapagos', 'Pacific/Galapagos'), (b'Pacific/Gambier', 'Pacific/Gambier'), (b'Pacific/Guadalcanal', 'Pacific/Guadalcanal'), (b'Pacific/Guam', 'Pacific/Guam'), (b'Pacific/Honolulu', 'Pacific/Honolulu'), (b'Pacific/Johnston', 'Pacific/Johnston'), (b'Pacific/Kiritimati', 'Pacific/Kiritimati'), (b'Pacific/Kosrae', 'Pacific/Kosrae'), (b'Pacific/Kwajalein', 'Pacific/Kwajalein'), (b'Pacific/Majuro', 'Pacific/Majuro'), (b'Pacific/Marquesas', 'Pacific/Marquesas'), (b'Pacific/Midway', 'Pacific/Midway'), (b'Pacific/Nauru', 'Pacific/Nauru'), (b'Pacific/Niue', 'Pacific/Niue'), (b'Pacific/Norfolk', 'Pacific/Norfolk'), (b'Pacific/Noumea', 'Pacific/Noumea'), (b'Pacific/Pago_Pago', 'Pacific/Pago Pago'), (b'Pacific/Palau', 'Pacific/Palau'), (b'Pacific/Pitcairn', 'Pacific/Pitcairn'), (b'Pacific/Ponape', 'Pacific/Ponape'), (b'Pacific/Port_Moresby', 'Pacific/Port Moresby'), (b'Pacific/Rarotonga', 'Pacific/Rarotonga'), (b'Pacific/Saipan', 'Pacific/Saipan'), (b'Pacific/Tahiti', 'Pacific/Tahiti'), (b'Pacific/Tarawa', 'Pacific/Tarawa'), (b'Pacific/Tongatapu', 'Pacific/Tongatapu'), (b'Pacific/Truk', 'Pacific/Truk'), (b'Pacific/Wake', 'Pacific/Wake'), (b'Pacific/Wallis', 'Pacific/Wallis'))), ('US', ((b'US/Alaska', 'US/Alaska'), (b'US/Arizona', 'US/Arizona'), (b'US/Central', 'US/Central'), (b'US/Eastern', 'US/Eastern'), (b'US/Hawaii', 'US/Hawaii'), (b'US/Mountain', 'US/Mountain'), (b'US/Pacific', 'US/Pacific'))), ('UTC', ((b'UTC', 'UTC'),))])),
                ('tags', grical.tagging.fields.TagField(blank=True, max_length=255, null=True, verbose_name='Tags', validators=[grical.events.utils.validate_tags_chars])),
                ('country', models.CharField(blank=True, max_length=2, null=True, verbose_name='Country', choices=[(b'AF', 'Afghanistan'), (b'AX', '\xc5land Islands'), (b'AL', 'Albania'), (b'DZ', 'Algeria'), (b'AS', 'American Samoa'), (b'AD', 'Andorra'), (b'AO', 'Angola'), (b'AI', 'Anguilla'), (b'AQ', 'Antarctica'), (b'AG', 'Antigua and Barbuda'), (b'AR', 'Argentina'), (b'AM', 'Armenia'), (b'AW', 'Aruba'), (b'AU', 'Australia'), (b'AT', 'Austria'), (b'AZ', 'Azerbaijan'), (b'BS', 'Bahamas'), (b'BH', 'Bahrain'), (b'BD', 'Bangladesh'), (b'BB', 'Barbados'), (b'BY', 'Belarus'), (b'BE', 'Belgium'), (b'BZ', 'Belize'), (b'BJ', 'Benin'), (b'BM', 'Bermuda'), (b'BT', 'Bhutan'), (b'BO', 'Bolivia, Plurinational State of'), (b'BA', 'Bosnia and Herzegovina'), (b'BW', 'Botswana'), (b'BV', 'Bouvet Island'), (b'BR', 'Brazil'), (b'IO', 'British Indian Ocean Territory'), (b'BN', 'Brunei Darussalam'), (b'BG', 'Bulgaria'), (b'BF', 'Burkina Faso'), (b'BI', 'Burundi'), (b'KH', 'Cambodia'), (b'CM', 'Cameroon'), (b'CA', 'Canada'), (b'CV', 'Cape Verde'), (b'KY', 'Cayman Islands'), (b'CF', 'Central African Republic'), (b'TD', 'Chad'), (b'CL', 'Chile'), (b'CN', 'China'), (b'CX', 'Christmas Island'), (b'CC', 'Cocos (Keeling) Islands'), (b'CO', 'Colombia'), (b'KM', 'Comoros'), (b'CG', 'Congo'), (b'CD', 'Congo, the Democratic Republic of the'), (b'CK', 'Cook Islands'), (b'CR', 'Costa Rica'), (b'CI', "C\xf4te d'Ivoire"), (b'HR', 'Croatia'), (b'CU', 'Cuba'), (b'CY', 'Cyprus'), (b'CZ', 'Czech Republic'), (b'DK', 'Denmark'), (b'DJ', 'Djibouti'), (b'DM', 'Dominica'), (b'DO', 'Dominican Republic'), (b'EC', 'Ecuador'), (b'EG', 'Egypt'), (b'SV', 'El Salvador'), (b'GQ', 'Equatorial Guinea'), (b'ER', 'Eritrea'), (b'EE', 'Estonia'), (b'ET', 'Ethiopia'), (b'FK', 'Falkland Islands (Malvinas)'), (b'FO', 'Faroe Islands'), (b'FJ', 'Fiji'), (b'FI', 'Finland'), (b'FR', 'France'), (b'GF', 'French Guiana'), (b'PF', 'French Polynesia'), (b'TF', 'French Southern Territories'), (b'GA', 'Gabon'), (b'GM', 'Gambia'), (b'GE', 'Georgia'), (b'DE', 'Germany'), (b'GH', 'Ghana'), (b'GI', 'Gibraltar'), (b'GR', 'Greece'), (b'GL', 'Greenland'), (b'GD', 'Grenada'), (b'GP', 'Guadeloupe'), (b'GU', 'Guam'), (b'GT', 'Guatemala'), (b'GG', 'Guernsey'), (b'GN', 'Guinea'), (b'GW', 'Guinea-Bissau'), (b'GY', 'Guyana'), (b'HT', 'Haiti'), (b'HM', 'Heard Island and McDonald Islands'), (b'VA', 'Holy See (Vatican City State)'), (b'HN', 'Honduras'), (b'HK', 'Hong Kong'), (b'HU', 'Hungary'), (b'IS', 'Iceland'), (b'IN', 'India'), (b'ID', 'Indonesia'), (b'IR', 'Iran, Islamic Republic of'), (b'IQ', 'Iraq'), (b'IE', 'Ireland'), (b'IM', 'Isle of Man'), (b'IL', 'Israel'), (b'IT', 'Italy'), (b'JM', 'Jamaica'), (b'JP', 'Japan'), (b'JE', 'Jersey'), (b'JO', 'Jordan'), (b'KZ', 'Kazakhstan'), (b'KE', 'Kenya'), (b'KI', 'Kiribati'), (b'KP', "Korea, Democratic People's Republic of"), (b'KR', 'Korea, Republic of'), (b'KW', 'Kuwait'), (b'KG', 'Kyrgyzstan'), (b'LA', "Lao People's Democratic Republic"), (b'LV', 'Latvia'), (b'LB', 'Lebanon'), (b'LS', 'Lesotho'), (b'LR', 'Liberia'), (b'LY', 'Libyan Arab Jamahiriya'), (b'LI', 'Liechtenstein'), (b'LT', 'Lithuania'), (b'LU', 'Luxembourg'), (b'MO', 'Macao'), (b'MK', 'Macedonia, the former Yugoslav Republic of'), (b'MG', 'Madagascar'), (b'MW', 'Malawi'), (b'MY', 'Malaysia'), (b'MV', 'Maldives'), (b'ML', 'Mali'), (b'MT', 'Malta'), (b'MH', 'Marshall Islands'), (b'MQ', 'Martinique'), (b'MR', 'Mauritania'), (b'MU', 'Mauritius'), (b'YT', 'Mayotte'), (b'MX', 'Mexico'), (b'FM', 'Micronesia, Federated States of'), (b'MD', 'Moldova, Republic of'), (b'MC', 'Monaco'), (b'MN', 'Mongolia'), (b'ME', 'Montenegro'), (b'MS', 'Montserrat'), (b'MA', 'Morocco'), (b'MZ', 'Mozambique'), (b'MM', 'Myanmar'), (b'NA', 'Namibia'), (b'NR', 'Nauru'), (b'NP', 'Nepal'), (b'NL', 'Netherlands'), (b'AN', 'Netherlands Antilles'), (b'NC', 'New Caledonia'), (b'NZ', 'New Zealand'), (b'NI', 'Nicaragua'), (b'NE', 'Niger'), (b'NG', 'Nigeria'), (b'NU', 'Niue'), (b'NF', 'Norfolk Island'), (b'MP', 'Northern Mariana Islands'), (b'NO', 'Norway'), (b'OM', 'Oman'), (b'PK', 'Pakistan'), (b'PW', 'Palau'), (b'PS', 'Palestinian Territory, Occupied'), (b'PA', 'Panama'), (b'PG', 'Papua New Guinea'), (b'PY', 'Paraguay'), (b'PE', 'Peru'), (b'PH', 'Philippines'), (b'PN', 'Pitcairn'), (b'PL', 'Poland'), (b'PT', 'Portugal'), (b'PR', 'Puerto Rico'), (b'QA', 'Qatar'), (b'RE', 'R\xe9union'), (b'RO', 'Romania'), (b'RU', 'Russian Federation'), (b'RW', 'Rwanda'), (b'BL', 'Saint Barth\xe9lemy'), (b'SH', 'Saint Helena'), (b'KN', 'Saint Kitts and Nevis'), (b'LC', 'Saint Lucia'), (b'MF', 'Saint Martin (French part)'), (b'PM', 'Saint Pierre and Miquelon'), (b'VC', 'Saint Vincent and the Grenadines'), (b'WS', 'Samoa'), (b'SM', 'San Marino'), (b'ST', 'Sao Tome and Principe'), (b'SA', 'Saudi Arabia'), (b'SN', 'Senegal'), (b'RS', 'Serbia'), (b'SC', 'Seychelles'), (b'SL', 'Sierra Leone'), (b'SG', 'Singapore'), (b'SK', 'Slovakia'), (b'SI', 'Slovenia'), (b'SB', 'Solomon Islands'), (b'SO', 'Somalia'), (b'ZA', 'South Africa'), (b'GS', 'South Georgia and the South Sandwich Islands'), (b'ES', 'Spain'), (b'LK', 'Sri Lanka'), (b'SD', 'Sudan'), (b'SR', 'Suriname'), (b'SJ', 'Svalbard and Jan Mayen'), (b'SZ', 'Swaziland'), (b'SE', 'Sweden'), (b'CH', 'Switzerland'), (b'SY', 'Syrian Arab Republic'), (b'TW', 'Taiwan, Province of China'), (b'TJ', 'Tajikistan'), (b'TZ', 'Tanzania, United Republic of'), (b'TH', 'Thailand'), (b'TL', 'Timor-Leste'), (b'TG', 'Togo'), (b'TK', 'Tokelau'), (b'TO', 'Tonga'), (b'TT', 'Trinidad and Tobago'), (b'TN', 'Tunisia'), (b'TR', 'Turkey'), (b'TM', 'Turkmenistan'), (b'TC', 'Turks and Caicos Islands'), (b'TV', 'Tuvalu'), (b'UG', 'Uganda'), (b'UA', 'Ukraine'), (b'AE', 'United Arab Emirates'), (b'GB', 'United Kingdom'), (b'US', 'United States'), (b'UM', 'United States Minor Outlying Islands'), (b'UY', 'Uruguay'), (b'UZ', 'Uzbekistan'), (b'VU', 'Vanuatu'), (b'VE', 'Venezuela, Bolivarian Republic of'), (b'VN', 'Viet Nam'), (b'VG', 'Virgin Islands, British'), (b'VI', 'Virgin Islands, U.S.'), (b'WF', 'Wallis and Futuna'), (b'EH', 'Western Sahara'), (b'WW', 'worldwide'), (b'YE', 'Yemen'), (b'ZM', 'Zambia'), (b'ZW', 'Zimbabwe')])),
                ('address', models.CharField(help_text='Complete address including city and country. Example:<br />Malm\xf6er Str. 6, Berlin, 10439, Germany', max_length=200, null=True, verbose_name='Location', blank=True)),
                ('city', models.CharField(max_length=50, null=True, verbose_name='City', blank=True)),
                ('coordinates', django.contrib.gis.db.models.fields.PointField(srid=4326, verbose_name='Coordinates', null=True, editable=False, blank=True)),
                ('exact', models.NullBooleanField(help_text='Indicates if the coordinates point to the exact location, or just to some near point within the same city or town', verbose_name='exact coordinates')),
                ('description', models.TextField(help_text='For formating use <a href="http://docutils.sourceforge.net/docs/user/rst/quickref.html">ReStructuredText</a> syntax. Events can be referenced with for instance :e:`123`', null=True, verbose_name='Description', blank=True)),
            ],
            options={
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
            },
        ),
        migrations.CreateModel(
            name='EventDate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('eventdate_name', models.CharField(help_text='Example: call for papers', max_length=80, verbose_name='Name')),
                ('eventdate_date', models.DateField(db_index=True, verbose_name='Date', validators=[grical.events.utils.validate_year])),
            ],
            options={
                'ordering': ['eventdate_date'],
            },
        ),
        migrations.CreateModel(
            name='EventSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('session_name', models.CharField(help_text='Example: day 2 of the conference', max_length=80, verbose_name='Session name')),
                ('session_date', models.DateField(verbose_name='Session day', validators=[grical.events.utils.validate_year])),
                ('session_starttime', models.TimeField(verbose_name='Session start time')),
                ('session_endtime', models.TimeField(verbose_name='Session end time')),
            ],
            options={
                'ordering': ['session_date', 'session_starttime'],
                'verbose_name': 'Session',
                'verbose_name_plural': 'Sessions',
            },
        ),
        migrations.CreateModel(
            name='EventUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url_name', models.CharField(help_text='Example: information about accomodation', max_length=80, verbose_name='URL Name')),
                ('url', models.URLField(verbose_name='URL')),
            ],
            options={
                'ordering': ['url_name'],
            },
        ),
        migrations.CreateModel(
            name='Filter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('modification_time', models.DateTimeField(auto_now=True, verbose_name='Modification time')),
                ('query', models.CharField(max_length=500, verbose_name='Query')),
                ('name', models.CharField(max_length=40, verbose_name='Name')),
                ('email', models.BooleanField(default=False, help_text='If set it sends an email to a user when a new event matches', verbose_name='Email')),
            ],
            options={
                'verbose_name': 'Filter',
                'verbose_name_plural': 'Filters',
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=80, verbose_name='Name', validators=[django.core.validators.RegexValidator(re.compile(b'.*[^0-9].*'), message='a group name must contain at least one character which is not a number')])),
                ('description', models.TextField(verbose_name='Description')),
                ('creation_time', models.DateTimeField(auto_now_add=True, verbose_name='Creation time')),
                ('modification_time', models.DateTimeField(auto_now=True, verbose_name='Modification time')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Group',
                'verbose_name_plural': 'Groups',
            },
        ),
        migrations.CreateModel(
            name='GroupInvitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('as_administrator', models.BooleanField(default=True, verbose_name='as administrator')),
                ('activation_key', models.CharField(max_length=40, verbose_name='activation key')),
                ('issue_date', models.DateField(auto_now_add=True, verbose_name='issue_date')),
                ('group', models.ForeignKey(verbose_name='group', to='events.Group')),
            ],
            options={
                'verbose_name': 'Group invitation',
                'verbose_name_plural': 'Group invitations',
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_administrator', models.BooleanField(default=True, verbose_name='Is administrator')),
                ('new_event_email', models.BooleanField(default=True, verbose_name='New event notification')),
                ('new_member_email', models.BooleanField(default=True, verbose_name='New member notification')),
                ('date_joined', models.DateField(auto_now_add=True, verbose_name='date_joined')),
                ('group', models.ForeignKey(related_name='membership', verbose_name='Group', to='events.Group')),
            ],
            options={
                'verbose_name': 'Membership',
                'verbose_name_plural': 'Memberships',
            },
        ),
        migrations.CreateModel(
            name='RevisionInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('as_text', models.TextField(null=True, blank=True)),
                ('redirect', models.IntegerField(null=True, blank=True)),
                ('reason', models.CharField(max_length=100, null=True, blank=True)),
                ('revision', models.ForeignKey(to='reversion.Revision')),
            ],
        ),
        migrations.CreateModel(
            name='ExtendedUser',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Recurrence',
            fields=[
                ('event', models.OneToOneField(related_name='_recurring', primary_key=True, serialize=False, to='events.Event', verbose_name='event')),
            ],
            options={
                'verbose_name': 'Recurrence',
                'verbose_name_plural': 'Recurrences',
            },
        ),
        migrations.AddField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(related_name='membership', verbose_name='User', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupinvitation',
            name='guest',
            field=models.ForeignKey(related_name='guest', verbose_name='host', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupinvitation',
            name='host',
            field=models.ForeignKey(related_name='host', verbose_name='host', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='group',
            name='events',
            field=models.ManyToManyField(to='events.Event', verbose_name='Events', through='events.Calendar'),
        ),
        migrations.AddField(
            model_name='group',
            name='members',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='Members', through='events.Membership'),
        ),
        migrations.AddField(
            model_name='filter',
            name='user',
            field=models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='eventurl',
            name='event',
            field=models.ForeignKey(related_name='urls', to='events.Event'),
        ),
        migrations.AddField(
            model_name='eventsession',
            name='event',
            field=models.ForeignKey(related_name='sessions', to='events.Event'),
        ),
        migrations.AddField(
            model_name='eventdate',
            name='event',
            field=models.ForeignKey(related_name='dates', to='events.Event'),
        ),
        migrations.AddField(
            model_name='event',
            name='user',
            field=models.ForeignKey(related_name='owner', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='User'),
        ),
        migrations.AddField(
            model_name='calendar',
            name='event',
            field=models.ForeignKey(related_name='calendar', verbose_name='Event', to='events.Event'),
        ),
        migrations.AddField(
            model_name='calendar',
            name='group',
            field=models.ForeignKey(related_name='calendar', verbose_name='Group', to='events.Group'),
        ),
        migrations.AddField(
            model_name='recurrence',
            name='master',
            field=models.ForeignKey(related_name='recurrences', verbose_name='master', to='events.Event'),
        ),
        migrations.AlterUniqueTogether(
            name='membership',
            unique_together=set([('user', 'group')]),
        ),
        migrations.AlterUniqueTogether(
            name='filter',
            unique_together=set([('user', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='eventurl',
            unique_together=set([('event', 'url_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='eventsession',
            unique_together=set([('event', 'session_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='eventdate',
            unique_together=set([('event', 'eventdate_name', 'eventdate_date')]),
        ),
        migrations.AlterUniqueTogether(
            name='calendar',
            unique_together=set([('event', 'group')]),
        ),
    ]
