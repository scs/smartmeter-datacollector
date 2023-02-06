# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import csv
import datetime
import os
from pathlib import Path
import time
from collections import deque
import asyncio
import logging

from ..smartmeter.meter_data import MeterDataPoint
from ..smartmeter.lge450 import LGE450_COSEM_REGISTERS
from ..smartmeter.iskraam550 import ISKRA_AM550_COSEM_REGISTERS
from ..smartmeter.cosem import RegisterCosem
from .data_sink import DataSink

LOGGER = logging.getLogger("sink")

class CsvSink(DataSink):
    """" Sink implementation for writing a daily csv file """
    # TODO: make CsvConfig dataclass and validation
    # TODO: implement weekly, monthly, yearly rotation
    # TODO: implement daily, weekly, monthly deletion    
    # TODO: implement appender with rolling FIFO retention
    # TODO: config for enable OBIS code header and/or name headers
    
    def __init__( self, config, section_name) -> None:
        self.directory = config[section_name].get("directory") # specify directory where the CSV files will be stored
        self.fieldnames, self.field_ids = self.get_fields(config)
        self.line_queue = deque()
        self.loop = None
        
    @staticmethod
    def get_fields(config):
        try:
            field_names = []
            field_ids = []
            meter_types = set()
            for section_name in filter(lambda sec: sec.startswith("reader"), config.sections()):
                meter_config = config[section_name]
                meter_types.add(meter_config.get('type'))
            for meter_type in meter_types:
                if meter_type == "lge450":
                    for point in LGE450_COSEM_REGISTERS:     
                        field_names.append(point.data_point_type.identifier.replace(",", "_"))
                        field_ids.append(point.obis)
                if meter_type == "iskraam550":
                    for point in ISKRA_AM550_COSEM_REGISTERS:
                        field_names.append(point.data_point_type.identifier.replace(",", "_"))
                        field_ids.append(point.obis)
        except:
            LOGGER.exception("Unable red fields during sink start")
            raise

        return field_names, field_ids

    async def start(self) -> None:
        # create directory if it doesn't exist
        Path(self.directory).mkdir(parents=True, exist_ok=True)

        await self.file_cleanup()
        self.loop = asyncio.create_task(self.line_loop())

    async def stop(self) -> None:
        self.loop.cancel()

    async def send(self, data_point: MeterDataPoint) -> None:
        self.line_queue.append(data_point)

    async def line_loop(self):
        """ buffer data_points to aggregate in one line """
        # TODO: find smarter time cirteria to aggregate
        while True:
            await asyncio.sleep(1)
            filename = await self.check_file_exists()

            aggregated_points = {}
   
           # TODO: aggragation per source 
           # TODO: aggragation per time frame
            while self.line_queue: 
                try:
                    data_point = self.line_queue.pop()
                    aggregated_points[data_point.type.identifier] = str(data_point.value).replace(",", "_")
                except Exception as e:
                    LOGGER.exception("Cannot pop line_queue")
        
            if len(aggregated_points) > 0:
                try:
                    line_data = [ data_point.timestamp.isoformat() , data_point.source ]
                    for key in self.fieldnames:
                        if key in aggregated_points:
                            line_data.append( str(aggregated_points[key]) )
                        else:
                            line_data.append("")

                    with open(os.path.join(self.directory, filename, ), 'a', newline='', encoding='utf-8') as csvfile:
                        new_line = ",".join(line_data)
                        csvfile.write(new_line + "\n")
                except:
                    LOGGER.exception("Failed to write line to csv file")
                else:
                    LOGGER.debug("Success writing line to csv file")
                        
    async def check_file_exists(self):
    
        # get current date and format it as a string
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # create filename using the current date
        filename = f'smartmeter_data_{today}.csv'
        
        # check if file already exists
        if not os.path.exists(os.path.join(self.directory, filename)):
            try:
                LOGGER.debug("Try to create csv file")
                # create file and write headers
                with open(os.path.join(self.directory, filename), 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                    writer.writeheader()
            except:
                LOGGER.exception("Failed to create csv file")
        return filename

    async def file_cleanup(self):
        # delete files older than one year
        try:
            for file in os.listdir(self.directory):
                if file.endswith(".csv"):
                    filepath = os.path.join(self.directory, file)
                    if os.path.getmtime(filepath) < (time.time() - 365 * 24 * 60 * 60):
                        os.remove(filepath)
        except:
            LOGGER.exception("Failed to cleanup csv file")
            