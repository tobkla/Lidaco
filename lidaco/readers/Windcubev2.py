import numpy as np
from pathlib import Path
from ..core.Reader import Reader
from datetime import datetime
import pandas as pd




class Windcubev2(Reader):

    def __init__(self):
        super().__init__(False)

    def str_to_num(self, string1):
        try:
            return int(string1)
        except ValueError:
            try:
                return float(string1)
            except ValueError:
                return string1

    def accepts_file(self, filename):
        return filename.endswith(('.sta','.rtd','.stdsta'))

    def output_filename(self, filename):
        return filename[:-4]
    
    def parse_time(self, string1):
        if self.parameters['filetype'] == 'rtd':
            temp = datetime.strptime(string1,'%Y/%m/%d %H:%M:%S.%f')
        else:
            temp = datetime.strptime(string1,'%Y/%m/%d %H:%M')
        return temp.isoformat() + 'Z'
        
    
    @staticmethod
    def get_timestamp(input_filepath, row_of_timestamp = 0 ):
        with open(input_filepath) as f:
            line = f.readlines()[42 + row_of_timestamp]
            
        filetype = input_filepath.split('.')[1]
        
        if filetype == 'rtd':
            timestamp = datetime.strptime(line.split('\t')[0], 
                                          '%Y/%m/%d %H:%M:%S.%f')
            
        elif filetype == 'sta':
            timestamp = datetime.strptime(line.split('\t')[0], 
                                          '%Y/%m/%d %H:%M')
            
        return timestamp
    
    

    def parse_azimuth(self, string1):
        if string1 == 'V':
            return 0
        else:
            return float(string1)
            
    def parse_elevation(self, string1):
        if string1 == 'V':
            return 90
        else:
            return 90 - self.parameters['ScanAngle (°)']
        

    def load_file(self, input_filepath):
        # read the file header and write to dict

        with open(input_filepath, encoding='latin-1') as f:
                header_length = int(f.readline().split('=')[1])
                parameters = [f.readline().split('=') for i in range(header_length)]
                
        parameters = {line[0]: self.str_to_num(line[1]) for line in parameters if len(line) == 2}
        parameters['Altitudes (m)'] = [self.str_to_num(element) for element in parameters['Altitudes (m)'].strip().split('\t')] 
        parameters['filetype'] = input_filepath[-3:]
        
        self.parameters = parameters
        
        df = pd.read_csv(input_filepath, skiprows = header_length + 1, sep='\t', decimal='.', converters={0:self.parse_time}, encoding='cp1252', index_col = False)

        if self.parameters['filetype'] == 'rtd':
            df['azimuth_angle']=df.Position.apply(self.parse_azimuth)
            df['elevation_angle']=df.Position.apply(self.parse_elevation)
    
        return df

    def create_variables(self, output_dataset):
        output_dataset.createDimension('range', len(self.parameters['Altitudes (m)']))
        output_dataset.createDimension('time', None)

        # create the coordinate variables
        range1 = output_dataset.createVariable('range', 'f4', ('range',))
        range1.units = 'm'
        range1.long_name = 'range_gate_distance_from_lidar'
        range1[:] = np.array(self.parameters['Altitudes (m)'])

        time = output_dataset.createVariable('time', str, ('time',))
        time.units = 's'
        time.long_name = 'Time UTC in ISO 8601 format yyyy-mm-ddThh:mm:ssZ'

        # create the beam steering and location variables
        yaw = output_dataset.createVariable('yaw', 'f4')
        yaw.units = 'degrees'
        yaw.long_name = 'lidar_yaw_angle'
        yaw[:] = self.parameters['DirectionOffset (°)']

        pitch = output_dataset.createVariable('pitch', 'f4')
        pitch.units = 'degrees'
        pitch.long_name = 'lidar_pitch_angle'
        pitch[:] = self.parameters['PitchAngle (°)']

        roll = output_dataset.createVariable('roll', 'f4')
        roll.units = 'degrees'
        roll.long_name = 'lidar_roll_angle'
        roll[:] = self.parameters['RollAngle (°)']

        # create the data variables
        scan_type = output_dataset.createVariable('scan_type', 'i')
        scan_type.units = 'none'
        scan_type.long_name = 'scan_type_of_the_measurement'

        accumulation_time = output_dataset.createVariable('accumulation_time', 'f4')
        accumulation_time.units = 'seconds'
        accumulation_time.long_name = 'time_for_spectral_accumulation'

        n_spectra = output_dataset.createVariable('n_spectra', 'f4')
        n_spectra.units = 'none'
        n_spectra.long_name = 'number_of_pulses'
        n_spectra[:] = self.parameters['Pulses / Line of Sight']

        # create the measurement variables
        if self.parameters['filetype'] == 'rtd':
            
            WS = output_dataset.createVariable('WS', 'f4', ('time', 'range'))
            WS.units = 'm.s-1'
            WS.long_name = 'scalar_wind_speed'
            
            DIR = output_dataset.createVariable('DIR', 'f4', ('time', 'range'))
            DIR.units = 'degrees'
            DIR.long_name = 'wind_direction'
            
            VEL = output_dataset.createVariable('VEL', 'f4', ('time', 'range'))
            VEL.units = 'm.s-1'
            VEL.long_name = 'radial_velocity'
            
            azimuth_angle = output_dataset.createVariable('azimuth_angle', 'f4', ('time'))
            azimuth_angle.units = 'degrees'
            azimuth_angle.long_name = 'azimuth_angle_of_lidar beam'
            
            elevation_angle = output_dataset.createVariable('elevation_angle', 'f4', ('time'))
            elevation_angle.units = 'degrees'
            elevation_angle.long_name = 'elevation_angle_of_lidar beam'
            				
            T_internal = output_dataset.createVariable('T_internal', 'f4', ('time',))
            T_internal.units = 'degrees C'
            T_internal.long_name = 'internal_temperature'
            
            T_external = output_dataset.createVariable('T_external', 'f4', ('time',))
            T_external.units = 'degrees C'
            T_external.long_name = 'external_temperature'
            
            p = output_dataset.createVariable('p', 'f4', ('time',))
            p.units = 'hPa'
            p.long_name = 'pressure'
            
            Rh = output_dataset.createVariable('Rh', 'f4', ('time',))
            Rh.units = 'percent'
            Rh.long_name = 'relative_humidity'

            CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
            CNR.units = 'dB'
            CNR.long_name = 'carrier_to_noise_ratio'
            				
            WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
            WIDTH.units = 'm.s-1'
            WIDTH.long_name = 'doppler_spectrum_width'
                            
            wiper = output_dataset.createVariable('wiper', 'f4', ('time',))
            wiper.units = 'V'
            wiper.long_name = 'Wiper count Vbatt'
            
            u = output_dataset.createVariable('u', 'f4', ('time', 'range'))
            u.units = 'm.s-1'
            u.long_name = 'u_component_of_wind_speed'
    
            v = output_dataset.createVariable('v', 'f4', ('time', 'range'))
            v.units = 'm.s-1'
            v.long_name = 'v_component_of_wind_speed'
    
            w = output_dataset.createVariable('w', 'f4', ('time', 'range'))
            w.units = 'm.s-1'
            w.long_name = 'w_component_of_wind_speed'

        else:
            WS = output_dataset.createVariable('WS', 'f4', ('time', 'range'))
            WS.units = 'm.s-1'
            WS.long_name = 'mean_of_scalar_wind_speed'
            				
            WSstd = output_dataset.createVariable('WSstd', 'f4', ('time', 'range'))
            WSstd.units = 'm.s-1'
            WSstd.long_name = 'standard_deviation_of_scalar_wind_speed'
            				
            WSmin = output_dataset.createVariable('WSmin', 'f4', ('time', 'range'))
            WSmin.units = 'm.s-1'
            WSmin.long_name = 'minimum_of_scalar_wind_speed'
            				
            WSmax = output_dataset.createVariable('WSmax', 'f4', ('time', 'range'))
            WSmax.units = 'm.s-1'
            WSmax.long_name = 'maximum_of_scalar_wind_speed'
            
            DIR = output_dataset.createVariable('DIR', 'f4', ('time', 'range'))
            DIR.units = 'degrees'
            DIR.long_name = 'mean_wind_direction'
            
            w = output_dataset.createVariable('w', 'f4', ('time', 'range'))
            w.units = 'm.s-1'
            w.long_name = 'mean_w_component_of_scalar_wind_speed'
            				
            wstd = output_dataset.createVariable('wstd', 'f4', ('time', 'range'))
            wstd.units = 'm.s-1'
            wstd.long_name = 'standard_deviation_of_w_component_of_scalar_wind_speed'
            				
            CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
            CNR.units = 'dB'
            CNR.long_name = 'mean_carrier_to_noise_ratio'
            
            CNRmin = output_dataset.createVariable('CNRmin', 'f4', ('time', 'range'))
            CNRmin.units = 'dB'
            CNRmin.long_name = 'minimum_carrier_to_noise_ratio'
            				
            WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
            WIDTH.units = 'm.s-1'
            WIDTH.long_name = 'mean_doppler_spectrum_width'
            
            Availability = output_dataset.createVariable('Availability', 'f4', ('time', 'range'))
            Availability.units = 'percent'
            Availability.long_name = 'data_availability'
            				
            T_internal = output_dataset.createVariable('T_internal', 'f4', ('time',))
            T_internal.units = 'degrees C'
            T_internal.long_name = 'mean_internal_temperature'
            				
            T_external = output_dataset.createVariable('T_external', 'f4', ('time',))
            T_external.units = 'degrees C'
            T_external.long_name = 'mean_external_temperature'
            
            p = output_dataset.createVariable('p', 'f4', ('time',))
            p.units = 'hPa'
            p.long_name = 'pressure'
            
            Rh = output_dataset.createVariable('Rh', 'f4', ('time',))
            Rh.units = 'percent'
            Rh.long_name = 'relative_humidity'	
            
            wiper = output_dataset.createVariable('wiper', 'f4', ('time',))
            wiper.units = 'V'
            wiper.long_name = 'Wiper count Vbatt'



    def write_file(self, output_dataset, df):
        output_dataset.variables['scan_type'][:] = 2
        output_dataset.variables['accumulation_time'][:] = 1.0
        
        if self.parameters['filetype'] == 'rtd': # high resolution data
            output_dataset.variables['time'][:] = df['Timestamp'].values
            output_dataset.variables['T_internal'][:] = df['Temperature'].values
            output_dataset.variables['wiper'][:] = df['Wiper Count'].values
            output_dataset.variables['azimuth_angle'][:] = df['azimuth_angle'].values
            output_dataset.variables['elevation_angle'][:] = df['elevation_angle'].values
            output_dataset.variables['WS'][:, :] = df.loc[:,['m Wind Speed (m/s)' in column for column in df.columns]]
            output_dataset.variables['DIR'][:, :] = df.loc[:,['Wind Direction (°)' in column for column in df.columns]]
            output_dataset.variables['VEL'][:, :] = df.loc[:,['Radial Wind Speed (m/s)' in column for column in df.columns]]
            output_dataset.variables['WIDTH'][:, :] = df.loc[:,['Radial Wind Speed Dispersion (m/s)' in column for column in df.columns]]
            output_dataset.variables['CNR'][:, :] = df.loc[:,['CNR (dB)' in column for column in df.columns]]
            output_dataset.variables['u'][:, :] = df.loc[:,['X-wind (m/s)' in column for column in df.columns]]
            output_dataset.variables['v'][:, :] = df.loc[:,['Y-wind (m/s)' in column for column in df.columns]]
            output_dataset.variables['w'][:, :] = df.loc[:,['Z-wind (m/s)' in column for column in df.columns]]

            
			# filetype == 'sta' # 10 minute mean values
        else:
            output_dataset.variables['time'][:] = df['Timestamp (end of interval)'].values
            output_dataset.variables['T_internal'][:] = df['Int Temp (°C)'].values
            output_dataset.variables['T_external'][:] = df['Ext Temp (°C)'].values
            output_dataset.variables['p'][:] = df['Pressure (hPa)'].values
            output_dataset.variables['Rh'][:] = df['Rel Humidity (%)'].values
            output_dataset.variables['wiper'][:] = df['Wiper count'].values
            output_dataset.variables['WS'][:, :] = df.loc[:,['Wind Speed (m/s)' in column for column in df.columns]]
            output_dataset.variables['WSstd'][:, :] = df.loc[:,['Wind Speed Dispersion (m/s)' in column for column in df.columns]]
            output_dataset.variables['WSmin'][:, :] = df.loc[:,['Wind Speed min (m/s)' in column for column in df.columns]]
            output_dataset.variables['WSmax'][:, :] = df.loc[:,['Wind Speed max (m/s)' in column for column in df.columns]]
            output_dataset.variables['DIR'][:, :] = df.loc[:,['Wind Direction (°)' in column for column in df.columns]]
            output_dataset.variables['w'][:, :] = df.loc[:,['Z-wind (m/s)' in column for column in df.columns]]
            output_dataset.variables['wstd'][:, :] = df.loc[:,['Z-wind Dispersion (m/s)' in column for column in df.columns]]
            output_dataset.variables['CNR'][:, :] = df.loc[:,['CNR (dB)' in column for column in df.columns]]
            output_dataset.variables['CNRmin'][:, :] = df.loc[:,['CNR min (dB)' in column for column in df.columns]]
            output_dataset.variables['WIDTH'][:, :] = df.loc[:,['Dopp Spect Broad (m/s)' in column for column in df.columns]]
            output_dataset.variables['Availability'][:, :] = df.loc[:,['Data Availability (%)' in column for column in df.columns]]
            
    def read_to(self, output_dataset, input_filepath, configs, appending):
        try:
            df = self.load_file(input_filepath)
            self.create_variables(output_dataset)
            self.write_file(output_dataset, df)
            
        except Exception as err:
            print('Error ocurred while converting %s. See error.log for details.' % input_filepath)
            print(err)
            with open(Path(output_dataset.filepath()).parent / 'error.log','a') as logfile:
                logfile.write( '%s'%output_dataset.filepath() +'\n')
                    
