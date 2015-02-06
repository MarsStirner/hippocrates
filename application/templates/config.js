WebMis20
.constant('WMConfig', {
    url: {

    },
    settings: {
        'user_idle_timeout': {{ settings.getInt('Auth.UserIdleTimeout', 5) }},
        'logout_warning_timeout': {{ settings.getInt('Auth.LogoutWarningTimeout', 200) }}
    }
});