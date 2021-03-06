from ..core.Reader import Reader
from ..common.Logger import Logger
from datetime import datetime, timedelta
import numpy as np
import os


class Windscanner(Reader):
    def __init__(self):
        super().__init__(False)

    @staticmethod
    def try_cast(variable, dtype=float):
        try:
            return dtype(variable)
        except Exception:
            return np.nan

    def accepts_file(self, filename):
        return filename.endswith('wind.txt') & (len(filename) > 14)

    def output_filename(self, timestamp):
        return os.path.split(timestamp)[-1][:-9]
    
    def get_timestamp(self, input_filepath, row_of_timestamp = 0 ):
        start_date = datetime(1904,1,1)
        
        with open(input_filepath) as f:
            line = f.readlines()[row_of_timestamp]
            
        timestamp_seconds = float(line.split(';')[4])
        timestamp = start_date + timedelta(seconds=timestamp_seconds)
        
        return timestamp
        
    def read_to(self, output_dataset, input_filepaths, parameters, appending):

        wind_file = input_filepaths
        system_file = wind_file[:wind_file.find('_wind.txt')] + '_system.txt'

        with open(wind_file) as f:
            wind_file_data = f.readlines()

        with open(system_file) as f:
            system_file_data = f.readlines()

        wind_file_data = [row.strip().split(';') for row in wind_file_data]
        system_file_data = [row.strip().split(';') for row in system_file_data]

        # check if file is corrupt by comparing the count of columns in each row
        columns_in_row = [len(row) for row in wind_file_data]
        median_columns = int(np.median(columns_in_row))
        column_differs = np.not_equal(columns_in_row, median_columns)
        any_column_differs = any(column_differs)
        
    
        if any_column_differs:
            wind_file_data = [row for row in wind_file_data if (len(row) == median_columns)]
            system_file_data = [row for row in system_file_data if (len(row) == median_columns)]
            Logger.warn('file_corrupt', os.path.split(wind_file)[1] )

        wind_file_data = list(zip(*wind_file_data))
        system_file_data = list(zip(*system_file_data))

        if not appending:
            index_columns = 4 - (len(wind_file_data) % 4)
            range_list = [float(row[0]) 
                            for row in wind_file_data[index_columns + 4::4]]

            # create the dimensions
            output_dataset.createDimension('range', len(range_list))
            output_dataset.createDimension('time', None)

            # create the coordinate variables

            # range
            range1 = output_dataset.createVariable('range', 'f4', ('range',))
            range1.units = 'm'
            range1.long_name = 'range_gate_distance_from_lidar'
            range1[:] = range_list
            range1.comment = ''

            # time
            time = output_dataset.createVariable('time', str, ('time',))
            time.units = 's'
            time.long_name = 'Time UTC in ISO 8601 format yyyy-mm-ddThh:mm:ssZ'
            time.comment = ''

            # create the data variables
            scan_type = output_dataset.createVariable('scan_type', 'i')
            scan_type.units = 'none'
            scan_type.long_name = 'scan_type_of_the_measurement'


            # create the measurement variables VEL, CNR, WIDTH
            VEL = output_dataset.createVariable('VEL', 'f4', ('time', 'range'))
            VEL.units = 'm.s-1'
            VEL.long_name = 'radial velocity'
            VEL.comment = ''
            VEL.accuracy = ''
            VEL.accuracy_info = ''

            CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
            CNR.units = 'dB'
            CNR.long_name = 'carrier-to-noise ratio'
            CNR.comment = ''
            CNR.accuracy = ''
            CNR.accuracy_info = ''




            WIDTH = output_dataset.createVariable('WIDTH', 'f4', 
                                                  ('time', 'range'))
            WIDTH.units = 'm.s-1'
            WIDTH.long_name = 'doppler spectrum width'
            WIDTH.comment = ''
            WIDTH.accuracy = ''
            WIDTH.accuracy_info = ''

            azimuth_angle = output_dataset.createVariable('azimuth_angle',
                                                          'f4', ('time'))
            azimuth_angle.units = 'degrees'
            azimuth_angle.long_name = 'azimuth_angle_of_lidar beam'
            azimuth_angle.comment = ''
            azimuth_angle.accuracy = ''
            azimuth_angle.accuracy_info = ''

            azimuth_sweep = output_dataset.createVariable('azimuth_sweep',
                                                          'f4', ('time'))
            azimuth_sweep.units = 'degrees'
            azimuth_sweep.long_name = 'azimuth_sector_swept' \
                                      '_during_accumulation'

            azimuth_sweep.comment = ''
            azimuth_sweep.accuracy = ''
            azimuth_sweep.accuracy_info = ''

            elevation_angle = output_dataset.createVariable(
                'elevation_angle', 'f4', ('time'))
            elevation_angle.units = 'degrees'
            elevation_angle.long_name = 'elevation_angle_of_lidar beam'
            elevation_angle.comment = ''
            elevation_angle.accuracy = ''
            elevation_angle.accuracy_info = ''

            elevation_sweep = output_dataset.createVariable(
                'elevation_sweep', 'f4', ('time'))

            elevation_sweep.units = 'degrees'
            elevation_sweep.long_name = 'elevation_sector_' \
                                        'swept_during_accumulation'

            elevation_sweep.comment = 'Elevation sweeping from ' \
                                      'approximately 0 to 15 degrees.'

            elevation_sweep.accuracy = ''
            elevation_sweep.accuracy_info = ''



            roll_angle = output_dataset.createVariable('roll_angle', 'f4', ('time'))
            roll_angle.units = 'degrees'
            roll_angle.long_name = 'roll angle of lidar'
            roll_angle.comment = ''
            roll_angle.accuracy = ''
            roll_angle.accuracy_info = ''

            pitch_angle = output_dataset.createVariable('pitch_angle', 'f4', ('time'))
            pitch_angle.units = 'degrees'
            pitch_angle.long_name = 'pitch angle of lidar'
            pitch_angle.comment = ''
            pitch_angle.accuracy = ''
            pitch_angle.accuracy_info = ''




            #%% get timestamps in ISO 8601 format
            start_date = datetime(1904, 1, 1)
            timestamp_seconds = [int(float(value.strip())) 
                                    for value in wind_file_data[index_columns]]
            
            timestamp_iso8601 = [(start_date +
                                  timedelta(seconds=value)).isoformat()+'Z' 
                                    for value in timestamp_seconds]
            
            output_dataset.variables['time'][:] = np.array(timestamp_iso8601)
            
            #%% calculate azimuth and elevation sweeps
            azimuth_angle_temp = [float(value) for value in wind_file_data[6]]
            
            elevation_angle_temp = [float(value) 
                                    for value in wind_file_data[7]]
            
            azimuth_sweep_temp = np.insert(np.abs(np.diff(azimuth_angle_temp)),
                                           0, np.nan)
            
            elevation_sweep_temp = np.insert(np.abs(
                                    np.diff(elevation_angle_temp)),0,np.nan)

            roll_temp = [float(value) for value in system_file_data[7]]
            pitch_temp = [float(value) for value in system_file_data[8]]




            beam_sweeping = (parameters['attributes']
                                ['beam_sweeping'] == 'true')
            
            if np.nanmedian(azimuth_sweep_temp) > 0:
                changing_azimuth = True
            else:
                changing_azimuth = False

            if np.nanmedian(elevation_sweep_temp) > 0:
                changing_elevation = True
            else:
                changing_elevation = False


            output_dataset.variables['azimuth_angle'][:] = azimuth_angle_temp
            output_dataset.variables['azimuth_sweep'][:] = azimuth_sweep_temp
            output_dataset.variables['elevation_angle'][:] = elevation_angle_temp
            output_dataset.variables['elevation_sweep'][:] = elevation_sweep_temp
            output_dataset.variables['roll_angle'][:] = roll_temp
            output_dataset.variables['pitch_angle'][:] = pitch_temp

            #%% setting scan_type according to sweeps 
            #case LOS
            if (not changing_azimuth) & (not changing_elevation): 
                scan_type[:] = 1
                
            #case DBS
            elif (changing_azimuth) & (not changing_elevation) \
                                    & (not beam_sweeping): 
                scan_type[:] = 2
            
            #case PPI
            elif (changing_azimuth) & (not changing_elevation) \
                                    & (beam_sweeping): 
                scan_type[:] = 4
                
            #case RHI
            elif (not changing_azimuth) & (changing_elevation) \
                                        & (beam_sweeping): 
                scan_type[:] = 5
                
            #case other
            else: 
                scan_type[:] = 0
            
         
            #%% read vel, width, cnr out of dataset
            # e.g. radial velocity starts at 5th column 
            # and is then repeated every 9th column
            output_dataset.variables['VEL'][:, :] = list(
                zip(*[[float(value) for value in row] 
                for row in wind_file_data[index_columns + 5::4]]))
                
            output_dataset.variables['CNR'][:, :] = list(
                zip(*[[float(value) for value in row] 
                for row in wind_file_data[index_columns + 6::4]]))
                
            output_dataset.variables['WIDTH'][:, :] = list(
                zip(*[[float(value) for value in row] 
                for row in wind_file_data[index_columns + 7::4]]))
            
        #%% case appending
        else: 
            index_columns = 4 - (len(wind_file_data) % 4)
            ntime = len(output_dataset.dimensions["time"])
            nrange = len(output_dataset.dimensions["range"])

            if nrange != len(wind_file_data[index_columns + 5::4]):
                Logger.warn('file_corrupt', os.path.split(wind_file)[1])
                return
            
            start_date = datetime(1904,1,1)
            timestamp_seconds = [int(float(value.strip())) 
                                for value in wind_file_data[index_columns]]
            
            timestamp_iso8601 = [ (start_date + 
                                   timedelta(seconds=value)).isoformat()+'Z' 
                                    for value in timestamp_seconds]
            
            
            output_dataset.variables['time'][ntime:] = np.array(timestamp_iso8601)
            
            azimuth_angle_temp = [float(value) for value in wind_file_data[6]]

            azimuth_sweep_temp = np.insert(np.abs(np.diff(azimuth_angle_temp)),0,np.nan)

            output_dataset.variables['azimuth_angle'][ntime:] = azimuth_angle_temp
            output_dataset.variables['azimuth_sweep'][ntime:] = azimuth_sweep_temp


            elevation_angle_temp = [float(value) for value in wind_file_data[7]]

            elevation_sweep_temp = np.insert(np.abs(np.diff(elevation_angle_temp)),0,np.nan)

            output_dataset.variables['elevation_angle'][ntime:] = elevation_angle_temp
            output_dataset.variables['elevation_sweep'][ntime:] = elevation_sweep_temp

            roll_temp = [float(value) for value in system_file_data[7]]
            pitch_temp = [float(value) for value in system_file_data[8]]
            output_dataset.variables['roll_angle'][:] = roll_temp
            output_dataset.variables['pitch_angle'][:] = pitch_temp


            output_dataset.variables['VEL'][ntime:, :] = list(
                    zip(*[[self.try_cast(value, float) for value in row]
                    for row in wind_file_data[index_columns + 5::4]]))

                
            output_dataset.variables['CNR'][ntime:, :] = list(
                    zip(*[[self.try_cast(value, float) for value in row]
                    for row in wind_file_data[index_columns + 6::4]]))
            
            output_dataset.variables['WIDTH'][ntime:, :] = list(
                    zip(*[[self.try_cast(value, float) for value in row]
                    for row in wind_file_data[index_columns + 7::4]]))
