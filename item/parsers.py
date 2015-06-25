#!/usr/bin/env python
#-*- coding: utf-8 -*-

import re
import sys
from item.models import Computer, HardDisk, CPU, GPU, Motherboard, Memory, NetworkAdapter
from django.utils import timezone

import os


def parse_inxi(data):
    # sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g"
    data = re.sub('\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]', '', data)
    #print(data)
    match = re.search('^System:(.*)^Machine:(.*)^CPU:(.*)^Graphics:(.*)^Audio:(.*)^Network:(.*)^Drives:(.*)^Info:(.*)', data, re.S | re.M)
    system = match.group(1)
    machine = match.group(2)
    cpu_line = match.group(3)
    graphics = match.group(4)
    audio = match.group(5)
    network = match.group(6)
    drives = match.group(7)
    info = match.group(8)

    hostname = re.match('\s+Host: (.*) Kernel', system).group(1)
    cpu = re.match('^\s+([\w ]+)\s+', cpu_line).group(1)
    (_, gpu_chipset, gpu_name) = re.match('^\s+Card(-\d)?: ([\w\s]+) \[(.*)\]', graphics).groups()
    (hd_model, hd_capacity, hd_unit) = re.match('^\s+.*model: (\w+) size: ([0-9\.]+)([TGB]+)', drives).groups()
    version = re.match('^\s+.*inxi: ([\d\.]+)', info).groups(1)

    try:
        (mobo_vendor, mobo_model) = re.match('^\s+.*System: (\w+) product: (\w+)', machine).groups()
    except AttributeError:
        (mobo_vendor, mobo_model) = re.match('^\s+.*Mobo: (\w+) model: ([\w ]+) Bios:', machine).groups()

    """
    print('hostname: %s' % hostname)
    print('cpu: %s' % cpu)
    print('mobo: %s %s' % (mobo_vendor, mobo_model))
    print('gpu: %s (%s)' % (gpu_name, gpu_chipset))
    print('hd: %s (%s%s)' % (hd_model, hd_capacity, hd_unit))
    print('version: %s' % version)
    """

    return {'hostname': hostname, 'cpu': cpu, 'gpu_chipset': gpu_chipset, 'gpu_name': gpu_name, 'hd_model': hd_model,
            'mobo_vendor': mobo_vendor, 'mobo_model': mobo_model,
            'hd_capacity': float(hd_capacity), 'hd_unit': hd_unit, 'version': version}


def parse_sysinfo(data):
    raise NotImplementedError


def create_computer_from_parser(content, user, format):

    if format == 'inxi':
        computer_dict = parse_inxi(content)
    elif format == 'sysinfo':
        computer_dict = parse_sysinfo(content)
    else:
        raise ValueError('Invalid format: %s' % format)

    try:
        Computer.objects.get(name=computer_dict['hostname'], user=user)
        return None
    except Computer.DoesNotExist:
        pass

    try:
        gpu = GPU.objects.get(name=computer_dict['gpu_name'])
    except GPU.DoesNotExist:
        if 'NVIDIA' in computer_dict['gpu_chipset']:
            gpu_vendor = 'NVIDIA'
        elif 'ATI' in computer_dict['gpu_chipset']:
            gpu_vendor = 'ATI'
        else:
            gpu_vendor = 'Unknown'
        gpu = GPU.objects.create(name=computer_dict['gpu_name'], vendor=gpu_vendor)

    try:
        cpu = CPU.objects.get(name=computer_dict['cpu'])
    except CPU.DoesNotExist:
        if 'Intel' in computer_dict['cpu']:
            cpu_vendor = 'Intel'
        elif 'AMD' in computer_dict['cpu']:
            cpu_vendor = 'AMD'
        else:
            cpu_vendor = 'Unknown'
        cpu = CPU.objects.create(name=computer_dict['cpu'], model=computer_dict['cpu'], vendor=cpu_vendor)

    try:
        hd = HardDisk.objects.get(model=computer_dict['hd_model'])
    except HardDisk.DoesNotExist:
        assert (computer_dict['hd_unit'] == 'GB')
        hd = HardDisk.objects.create(name=computer_dict['hd_model'], model=computer_dict['hd_model'],
                                     capacity_gb=computer_dict['hd_capacity'])

    mobo, _ = Motherboard.objects.get_or_create(vendor=computer_dict['mobo_vendor'], name=computer_dict['mobo_model'])
    generic_memory = Memory.objects.get(name='Generic', capacity_mb=1024)
    generic_network = NetworkAdapter.objects.get(name='Generic', speed='1 Gbps')

    now = timezone.now()
    computer = Computer(name=computer_dict['hostname'], user=user)
    computer.is_laptop = False
    computer.is_public = True
    computer.cpu = cpu
    computer.mobo = mobo
    computer.gpu = gpu
    computer.hd = hd
    computer.memory = generic_memory
    computer.network = generic_network
    computer.created_at = now
    computer.updated_at = now
    computer.year = now.year
    computer.save()

    filename = "info_%d-%s-%s.txt" % (computer.id, computer.user, now)
    filename = os.path.join('uploads', os.path.join('infos', filename))
    with open(filename, 'wb+') as fp:
        fp.write(content)

    return computer


if __name__ == '__main__':
    fp = open(sys.argv[1], 'r')
    parse_inxi(fp.read())
