# Restbus simulation capable to read and send back SecOC packets ith counter.
# !/usr/bin/python3

import os
import sys
import datetime
import time
from threading import Thread


def Log(str_text, end='\n'):
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    formatted_str = ("[%s] %s%s" % (st, str_text, end))
    sys.stdout.write(str(formatted_str))
    sys.stdout.flush()


class SecOC_Restbus:
    def __init__(self, can_channel, key):
        self._can_channel = can_channel
        self._key = str(key).replace(" ", "")
        self._counter_started = False
        self._counter_can_id = 0x00
        self._counter = 0
        # Used to inform other threads when application is shutting down
        self._shutdown = False

        # Start workers
        self._worker_ctr_main = Thread(target=self.CounterMainFunction, name="Counter broadcast messages", args=[])
        self._worker_ctr_main.daemon = True
        self._worker_ctr_main.start()

    def __del__(self):
        self._shutdown = True
        # Wait for workers to finish before leaving
        while self._worker_ctr_main.is_alive():
            time.sleep(0.001)

    def __IncrementCounter(self):
        if self._counter + 1 == 0xFFFFFFFF:
            self._counter = 0
        else:
            self._counter += 1

    def __GetMillisSinceEpoch(self):
        return int(time.time_ns() // 1000000)

    def CounterMainFunction(self):
        last_send_timestamp = 0
        while not self._shutdown:
            if self._counter_started:
                # Broadcast Counter every 200ms
                curr_time = self.__GetMillisSinceEpoch()
                if curr_time - last_send_timestamp >= 200:
                    last_send_timestamp = curr_time
                    self.__IncrementCounter()
                    Log("TickCount: %d" % self._counter)

            # Prevent CPU from getting crazy
            time.sleep(0.001)

    def StartCounterBroadcast(self, custom_counter_val=None):
        self._counter_started = True

    def StopCounterBroadcast(self):
        self._counter_started = False

    def SetCounterAddressCAN(self, counter_can_id):
        self._counter_can_id = counter_can_id

    def SetCounter(self, new_counter_val):
        self._counter = new_counter_val

    def GetCounter(self):
        pass


def main():
    restbus = SecOC_Restbus("can0", "1E A7 6A C0 04 BC 95 9A BB 1E E9 A1 8D AF B6 FE")
    restbus.SetCounterAddressCAN(0x3A)
    restbus.StartCounterBroadcast()

    Log("Wait 1 s...")
    time.sleep(1)
    Log("Timeout, application will close")

# Execute main function
if __name__ == '__main__':
    try:
        os.system('color')  # Enable terminal colors
        main()
    except KeyboardInterrupt:
        print('Keyboard interrupt detected! Program will end now... ', file=sys.stderr)
        # Wait for last write to be fully finished
        sys.exit(1)