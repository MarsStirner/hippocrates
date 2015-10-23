# -*- coding: utf-8 -*-

from nemesis.models.enums import MeasureStatus


em_final_status_list = (MeasureStatus.performed[0], MeasureStatus.overdue[0], MeasureStatus.cancelled[0],
                        MeasureStatus.cancelled_dupl[0], MeasureStatus.cancelled_changed_data[0])
