$('form').submit(function(){
    $('body').addClass("loading");
});

function processSchedule(schedule, attendance_types) {
    var my_schedule = {};
    var my_max_tickets = {};
    attendance_types.map(function (attype) {
        my_schedule[attype.code] = schedule.map(function (day) {
            return {
                id: day.id,
                date: day.date,
                office: day.office,
                tickets: []
            };
        });
        my_max_tickets[attype.code] = 0;
    });

    schedule.map(function (day, day_n) {
        day.tickets.map(function (ticket) {
            my_schedule[ticket.attendance_type][day_n].tickets.push(ticket);
        })
    });

    attendance_types.map(function (attype) {
        my_max_tickets[attype.code] = Math.max.apply(
            0,
            my_schedule[attype.code].map(function (day) {
                return day.tickets.length;
            })
        );
    });
    return {
        schedules: my_schedule,
        max_tickets: my_max_tickets
    }
}