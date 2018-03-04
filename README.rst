socos
=====

socos (Sonos Controller Shell) is a commandline tool for controlling
Sonos speakers.

Build
=====

.. image:: https://travis-ci.org/SoCo/socos.svg?branch=master
   :target: https://travis-ci.org/SoCo/socos
   :alt: Build Status

.. image:: https://requires.io/github/SoCo/socos/requirements.png?branch=master
   :target: https://requires.io/github/SoCo/socos/requirements/?branch=master
   :alt: Requirements Status

.. image:: https://img.shields.io/pypi/dm/socos.svg
   :target: https://pypi.python.org/pypi/socos/
   :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/v/socos.svg
   :target: https://pypi.python.org/pypi/socos/
   :alt: Number of PyPI downloads


Usage example
=============

A typical session (instead of `tracks enough add 1` you could also do `tracks enough replace 1` to replace the queue instead of adding to the end.

.. code-block::

  socos> list
  (1) 192.168.1.101 Living room
  (2) 192.168.1.102 Bathroom
  socos> set 1
  socos(Living room|Stopped)> tracks enough
  (1) Don't stop til you get enough by Michal Jackson
  (2) No more tears (enough is enough) by Barbra Streisand
  socos(Living room|Stopped)> tracks enough add 1
  Added tracks to queue: 'Don't stop til you get enough'
  socos(Living room|Stopped)> queue
  1: Michael Jackson - Don't stop til you get enough
  socos(Living room|Stopped)> play
  socos(Living room|Playing)> volume
  20
  socos(Living room|Playing)> volume +10
  30

