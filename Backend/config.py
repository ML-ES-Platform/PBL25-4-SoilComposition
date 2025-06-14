DB_PARAMS = {
    'host': 'localhost',
    'user': 'postgres',
    'password': 'alexandrina',
    'port': 5432,
    'database': 'iot_data'
}

MQTT_PARAMS = {
    'broker': '9e862c744fbd4909800bc2d576a7fd78.s1.eu.hivemq.cloud',
    'port': 8883, # Usually 8883 for secure TLS connection
    'topic': "sensors/moisture/#",
    'username': 'alexandrina',
    'password': 'PBL_iot_223'
} 