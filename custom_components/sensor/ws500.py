"""
Support for WS300/500 weather station queries to perl script

"""
import subprocess
from datetime import timedelta
import logging
import json

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_NAME, CONF_VALUE_TEMPLATE, CONF_UNIT_OF_MEASUREMENT, CONF_COMMAND,
STATE_UNKNOWN, CONF_MONITORED_CONDITIONS)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.util import dt as dt_util


_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ws500'
DEPENDENCIES = []

DEFAULT_COMMAND = 'ssh -i /home/willhaus/.ssh/id_rsa pi@weatherpi ws500 | tail -n1'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

SENSOR_TYPES = {
    'temperature0': ['Temperature 0', '°C', 0],
    'humidity0': ['Humidity 0', '%', 1],
    'temperature1': ['Temperature 1', '°C', 2],
    'humidity1': ['Humidity 1', '%', 3],
    'temperature2': ['Temperature 2', '°C', 4],
    'humidity2': ['Humidity 2', '%', 5],
    'temperature3': ['Temperature 3', '°C', 6],
    'humidity3': ['Humidity 3', '%', 7],
    'temperature4': ['Temperature 4', '°C', 8],
    'humidity4': ['Humidity 4', '%', 9],
    'temperature5': ['Temperature 5', '°C', 10],
    'humidity5': ['Humidity 5', '%', 11],
    'temperature6': ['Temperature 6', '°C', 12],
    'humidity6': ['Humidity 6', '%', 13],
    'temperature7': ['Temperature 7', '°C', 14],
    'humidity7': ['Humidity 7', '%', 15],
    'temperature8': ['Temperature 8', '°C', 16],
    'humidity8': ['Humidity 8', '%', 17],
    'temperature9': ['Temperature 9', '°C', 18],
    'humidity9': ['Humidity 9', '%', 19],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_COMMAND, default=DEFAULT_COMMAND): cv.string,
    vol.Optional(CONF_MONITORED_CONDITIONS, default=['temperature0', 'humidity0']):
vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the WS500 Sensor."""
    command = config.get(CONF_COMMAND, DEFAULT_COMMAND)
    data = Ws500SensorData(command)

    sensors = []
    for variable in config[CONF_MONITORED_CONDITIONS]:
        sensors.append(Ws500Sensor(data, variable))

    _LOGGER.info("Monitored sensors: %s", str(sensors))
    try:
        data.update()
    except ValueError as err:
        _LOGGER.error("Received error from WS500: %s", err)
        return False

    add_devices(sensors)
    return True


class Ws500Sensor(Entity):
    """Representation of Ws500 sensor."""

    def __init__(self, data, variable):
        """Initialize the sensor."""
        self.client_name = 'WS500'
        self.data = data
        self._name = SENSOR_TYPES[variable][0]
        self.type = variable[:-1]
        self._state = None
        self._unit_of_measurement = SENSOR_TYPES[variable][1]
        self.index = SENSOR_TYPES[variable][2]

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self.client_name, self._name)

    @property
    def state(self):
        """Return the state of the device."""

        if self.data.data is not None:
            return self.data.data[self.index]
        else:
            return STATE_UNKNOWN


    def update(self):
        """Get the latest data and updates the state."""
        self.data.update()
        #value = self.data.data

        #if value is None:
        #    value = STATE_UNKNOWN
        #elif self._value_template is not None:
        #    self._state = self._value_template.render_with_possible_json_value(
        #        value, STATE_UNKNOWN)
        #else:
        #    self._state = value


    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
        }

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement


class Ws500SensorData(object):
    """The class for handling the data retrieval."""

    def __init__(self, command):
        """Initialize the data object."""
        self.command = command
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data with a shell command."""
        _LOGGER.info('Updating data from WS500')

        try:
            return_value = subprocess.check_output(self.command, shell=True,
                                                   timeout=60)
            self.data = json.loads(return_value.strip().decode('utf-8'))
        except subprocess.CalledProcessError:
            _LOGGER.error('Command failed: %s', self.command)
        except subprocess.TimeoutExpired:
            _LOGGER.error('Timeout for command: %s', self.command)

