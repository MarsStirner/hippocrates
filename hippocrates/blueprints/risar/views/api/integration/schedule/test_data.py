# coding: utf-8

create_scheds_data = {
    'lpu_code': '-2',
    'doctor_code': '999',
    'scheds': [
        {
            "date": "2016-10-01",
            "intervals": [
                {
                    "begin_time": "09:00",
                    "end_time": "15:00",
                    "quantity": 7
                },
                {
                    "begin_time": "17:00",
                    "end_time": "19:00",
                    "quantity": 3
                }
            ]
        },
        {
            "date": "2016-10-02",
            "intervals": [
                {
                    "begin_time": "10:00",
                    "end_time": "17:00",
                    "quantity": 20
                }
            ]
        },
        {
            "date": "2016-10-31",
            "intervals": [
                {
                    "begin_time": "10:00",
                    "end_time": "17:00",
                    "quantity": 20
                }
            ]
        }
    ]
}


schedule_full_data = {
    'hospital': '-2',
    'doctor': '999',
    'date': '2016-12-17',
    'time_begin': '10:00',
    'time_end': '15:00',
    'schedule_tickets': [
        {
            'time_begin': '10:00',
            'time_end': '10:30'
        },
        {
            'time_begin': '10:30',
            'time_end': '11:30',
            'patient': '297'
        },
        {
            'time_begin': '11:45',
            'time_end': '12:30'
        }
    ]
}
