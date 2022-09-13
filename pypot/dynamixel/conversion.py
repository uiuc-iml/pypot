# -*- coding: utf-8 -*-


"""
    This module describes all the conversion method used to transform value from the representation used by the dynamixel motor to a more standard form (e.g. degrees, volt...).

    For compatibility issue all comparison method should be written in the following form (even if the model is not actually used):
        * def my_conversion_from_dxl_to_si(value, model): ...
        * def my_conversion_from_si_to_dxl(value, model): ...

    .. note:: If the control is readonly you only need to write the dxl_to_si conversion.

    """

import numpy
import itertools
import time
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# MARK: - Position

position_range = {
    'MX': (4096, 360.0),
    'SR': (4096, 360.0),
    'EX': (4096, 251.0),
    'XM':(4096,360.0),
    '*': (1024, 300.0)
}

torque_max = {  # in N.m
    'MX-106': 8.4,
    'MX-64': 6.,
    'MX-28': 2.5,
    'MX-12': 1.2,
    'AX-12': 1.2,
    'AX-18': 1.8,
    'RX-24': 2.6,
    'RX-28': 2.5,
    'RX-64': 4.,
    'XL-320': 0.39,
    'SR-RH4D': 0.57,
    'EX-106': 10.9,
    'XM-430':4.1
}

velocity = {  # in degree/s
    'MX-106': 270.,
    'MX-64': 378.,
    'MX-28': 330.,
    'MX-12': 2820.,
    'AX-12': 354.,
    'AX-18': 582.,
    'RX-24': 756.,
    'RX-28': 402.,
    'RX-64': 294.,
    'SR-RH4D': 300.,
    'XM-430':276.
}


def dxl_to_degree(value, model):
    determined_model = '*'
    if model.startswith('MX'):
        determined_model = 'MX'
    elif model.startswith('SR'):
        determined_model = 'SR'
    elif model.startswith('EX'):
        determined_model = 'EX'
    elif model.startswith('XM'):
        determined_model = 'XM'
    max_pos, max_deg = position_range[determined_model]

    return round(((max_deg * float(value)) / (max_pos - 1)) - (max_deg / 2), 2)


def degree_to_dxl(value, model):
    determined_model = '*'
    if model.startswith('MX'):
        determined_model = 'MX'   
    elif model.startswith('SR'):
        determined_model = 'SR'
    elif model.startswith('EX'):
        determined_model = 'EX'
    elif model.startswith('XM'):
        determined_model = 'XM'
    max_pos, max_deg = position_range[determined_model]

    pos = int(round((max_pos - 1) * ((max_deg / 2 + float(value)) / max_deg), 0))
    pos = min(max(pos, 0), max_pos - 1)

    return pos

def dxl_to_multi_degree(value,model):
    # print('receiving this pos value = {}'.format(value))

    if(value > 4294967296/2):
        value = (value - 4294967296)
    else:
        value = value
    return 0.088*value

def multi_degree_to_dxl(value,model):

    if(value < 0):
        pos = 4294967296 + value/0.088
    else:
        pos = value/0.088
    # print('sending this pos: {} , which is read as {}'.format(pos,dxl_to_multi_degree(pos,None)))

    return int(numpy.round((numpy.clip(pos,0,4294967296))))

# MARK: - Speed


def dxl_to_speed(value, model):
    # cw, speed = divmod(value, 1024)
    # direction = (-2 * cw + 1)

    speed_factor = 0.111
    if model.startswith('MX') or model.startswith('SR'):
        speed_factor = 0.114
    elif(model.startswith('XM')):
        speed_factor = 0.229
    # print('this is the value I got {}'.format(value))
    if(value > 4294967296/2):
        velocity = (value - 4294967296)
    else:
        velocity = value
    return velocity*speed_factor


def speed_to_dxl(value, model):
    # direction = 1024 if value < 0 else 0
    speed_factor = 0.111
    if model.startswith('MX') or model.startswith('SR'):
        speed_factor = 0.114
    elif(model.startswith('XM')):
        speed_factor = 0.229

    # max_value = 1023 * speed_factor * 6
    # value = min(max(value, -max_value), max_value)
    if(value < 0):
        speed = 4294967296 + value/speed_factor
    else:
        speed = value/speed_factor
    # print('sending this speed:',speed)
    return int(numpy.round(speed))

# MARK: - Torque


def dxl_to_torque(value, model):

    if(model.startswith('XM')):
        return round(value*0.00269*1.66,1)
    else:
        return round(value / 10, 1)


def torque_to_dxl(value, model):
    return int(round(value * 10, 0))


def dxl_to_load(value, model):
    # print('processing this value {}'.format(value))
    if(value > 1000):
        load = value - 65536
    else:
        load = value
    return dxl_to_torque(load, model)

def dxl_to_ms(value,model):
    time_factor = 1
    if model.startswith('XM'):
        time_factor = 20
    return time_factor*value
def ms_to_dxl(value,model):
    time_factor = 1
    if model.startswith('XM'):
        time_factor = 20
    return value//time_factor
# MARK - Acceleration


def dxl_to_acceleration(value, model):
    """Converts from ticks to degress/second^2"""

    return value * 8.583  # degrees / sec**2


def acceleration_to_dxl(value, model):
    """Converts from degrees/second^2 to ticks"""

    return int(round(value / 8.583, 0))  # degrees / sec**2

# PID Gains


def dxl_to_pid(value, model):
    return (value[0] * 0.004,
            value[1] * 0.48828125,
            value[2] * 0.125)


def pid_to_dxl(value, model):
    def truncate(x):
        return int(max(0, min(x, 254)))
    return [truncate(x * y) for x, y in zip(value, (250, 2.048, 8.0))]

# MARK: - Model


dynamixelModels = {
    12: 'AX-12',    # 12 + (0<<8)
    18: 'AX-18',    # 18 + (0<<8)
    24: 'RX-24',    # 24 + (0<<8)
    28: 'RX-28',    # 28 + (0<<8)
    29: 'MX-28',    # 29 + (0<<8)
    30: 'MX-28',    # 30 + (0<<8)
    64: 'RX-64',    # 64 + (0<<8)
    107: 'EX-106',
    360: 'MX-12',   # 104 + (1<<8)
    310: 'MX-64',   # 54 + (1<<8)
    320: 'MX-106',  # 64 + (1<<8)
    350: 'XL-320',  # 94 + (1<<8)
    400: 'SR-RH4D',
    401: 'SR-RH4D',  # Virtual motor
    1020:'XM-430'
}


def dxl_to_model(value, dummy=None):
    return dynamixelModels[value]
# MARK: - Drive Mode


def check_bit(value, offset):
    return bool(value & (1 << offset))


def dxl_to_drive_mode(value, model):
    return ('reverse' if check_bit(value, 0) else 'normal',
            'slave' if check_bit(value, 1) else 'master')


def drive_mode_to_dxl(value, model):
    return (int('slave' in value) << 1 | int('reverse' in value))

def dxl_to_load_velocity_position(value,model):
    load = dxl_to_load(value%65536,model)
    velocity = dxl_to_speed(((value>>16)%4294967296),model)
    position = dxl_to_degree(((value>>48)%4294967296),model)
    return(load,velocity,position)
# MARK: - Baudrate

def dxl_to_load_velocity_multi_position(value,model):
    load = dxl_to_load(value%65536,model)
    velocity = dxl_to_speed(((value>>16)%4294967296),model)
    position = dxl_to_multi_degree(((value>>48)%4294967296),model)
    return(load,velocity,position)


dynamixelBaudrates = {
    1: 1000000.0,
    3: 500000.0,
    4: 400000.0,-
    16: 117647.1,
    34: 57600.0,
    103: 19230.8,
    207: 9615.4,
    250: 2250000.0,
    251: 2500000.0,
    252: 3000000.0,
}

dynamixelBaudratesWithModel = {
    'XL-320': {
        0: 9600.0,
        1: 57600.0,
        2: 115200.0,
        3: 1000000.0
    }
}


def dxl_to_baudrate(value, model):
    return dynamixelBaudratesWithModel.get(model, dynamixelBaudrates)[value]


def baudrate_to_dxl(value, model):
    current_baudrates = dynamixelBaudratesWithModel.get(model, dynamixelBaudrates)
    for k, v in current_baudrates.items():
        if (abs(v - value) / float(value)) < 0.05:
            return k
    raise ValueError('incorrect baudrate {} (possible values {})'.format(value, list(current_baudrates.values())))

# MARK: - Return Delay Time


def dxl_to_rdt(value, model):
    return value * 2


def rdt_to_dxl(value, model):
    return int(value / 2)

def ms_to_dxl(value,model):
    return int(value/20)

def dxl_to_ms(value,model):
    return value*20

# MARK: - Temperature


def dxl_to_temperature(value, model):
    return float(value)


def temperature_to_dxl(value, model):
    return int(value)

# MARK: - Current


def dxl_to_current(value, model):
    if model.startswith('SR'):
        # The SR motors do use a different conversion formula than the dynamixel motors
        # See http://kb.seedrobotics.com/doku.php?id=dh4d:dynamixelcontroltables
        return (value * 0.4889) / 1000.0
    else:
        return 4.5 * (value - 2048.0) / 1000.0

# MARK: - Voltage


def dxl_to_voltage(value, model):
    return value * 0.1


def voltage_to_dxl(value, model):
    return int(value * 10)

# MARK: - Status Return Level


status_level = ('never', 'read', 'always')


def dxl_to_status(value, model):
    return status_level[value]


def status_to_dxl(value, model):
    if value not in status_level:
        raise ValueError('status "{}" should be chosen among {}'.format(value, status_level))
    return status_level.index(value)

# MARK: - Error

# TODO: depend on protocol v1 vs v2


dynamixelErrors = ['None Error',
                   'Instruction Error',
                   'Overload Error',
                   'Checksum Error',
                   'Range Error',
                   'Overheating Error',
                   'Angle Limit Error',
                   'Input Voltage Error']


def dxl_to_alarm(value, model):
    return decode_error(value)


def decode_error(error_code):
    bits = numpy.unpackbits(numpy.asarray(error_code, dtype=numpy.uint8))
    return tuple(numpy.array(dynamixelErrors)[bits == 1])


def alarm_to_dxl(value, model):
    if not set(value).issubset(dynamixelErrors):
        raise ValueError('should only contains error among {}'.format(dynamixelErrors))

    indices = [len(dynamixelErrors) - 1 - dynamixelErrors.index(e) for e in value]
    return sum(2 ** i for i in indices)


XL320LEDColors = Enum('Colors', 'off red green yellow '
                      'blue pink cyan white')


def dxl_to_led_color(value, model):
    return XL320LEDColors(value + 1).name


def led_color_to_dxl(value, model):
    value = getattr(XL320LEDColors, value).value - 1
    value = int(value) & 0b111
    return value


control_modes = {
    1: 'velocity',
    3: 'position',
    4: 'extended_position'
}


def dxl_to_control_mode(value, _):
    return control_modes[value]


def control_mode_to_dxl(mode, _):
    logger.debug('converting mode')
    return (next((v for v, m in control_modes.items()
                  if m == mode), None))

# MARK: - Various utility functions


def dxl_to_bool(value, model):
    return bool(value)


def bool_to_dxl(value, model):
    return int(value)


def dxl_decode(data):
    if len(data) == 0:
        raise ValueError('try to decode incorrect data {}'.format(data))
    
    # if len(data) == 1:
    #     return data[0]

    # if len(data) == 2:
    #     return data[0] + (data[1] << 8)
    
    # if len(data) == 4:
    #     return data[0] + (data[1]<<8) + (data[])
    output = 0
    # print('\n\nthis is data {}\n\n'.format(data))
    for i in range(len(data)):
        output += (data[i] << (8*i))
        # print('this is output now',output)
    return output

def dxl_decode_all(data, nb_elem):
    if nb_elem > 1:
        data = list(zip(*([iter(data)] * (len(data) // nb_elem))))
        return tuple(map(dxl_decode, data))
    else:
        return dxl_decode(data)


def dxl_code(value, length):
    start_time = time.time()
    if length <= 0:
        raise ValueError('try to code value with an incorrect length {}'.format(length))

    # if length == 1:
    #     return (value, )

    # if length == 2:
    #     return (value % 256, value >> 8)
    result = length*[0]
    # print(value)
    for i in range(length):
        result[i]  = ((value >> (8*i))%256)
    # print('decoding took {}'.format(time.time()-start_time))
    return tuple(result)

def dxl_code_all(value, length, nb_elem):
    if nb_elem > 1:
        return list(itertools.chain(*(dxl_code(v, length) for v in value)))
    else:
        return dxl_code(value, length)
