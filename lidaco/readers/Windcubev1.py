import datetime
import numpy as np
from pathlib import Path
from lidaco.core.Reader import Reader
import os
import pandas as pd



class Windcubev1(Reader):
    def __init__(self):
        super().__init__(False)

    def parse_time(self, string1):
        if self.parameters['filetype'] == 'rtd':
            temp = datetime.datetime.strptime(string1,'%d/%m/%Y %H:%M:%S.%f')
        else:
            temp = datetime.datetime.strptime(string1,'%d/%m/%Y %H:%M:%S')
        return temp.isoformat() + 'Z'
    
    @staticmethod
    def str_to_num(string1):
        try:
            return int(string1)
        except ValueError:
            try:
                return float(string1)
            except ValueError:
                return string1

    def accepts_file(self, filename):
        return filename.endswith(('.sta','.rtd'))

    def output_filename(self, filename):
        return filename[:-4]
    
    def load_file(self, input_filepath):
        # read the file header and write to dict

        with open(input_filepath, encoding='latin-1') as f:
                header_length = int(f.readline().split('=')[1])
                parameters = [f.readline().split('=') for i in range(header_length)]
                
        parameters = {line[0]: self.str_to_num(line[1]) for line in parameters if len(line) == 2}
        parameters['Altitudes(m)'] = [self.str_to_num(element) for element in parameters['Altitudes(m)'].strip().split('\t')] 
        parameters['filetype'] = input_filepath[-3:]
        
        self.parameters = parameters
        df = pd.read_csv(input_filepath, skiprows = header_length + 1, sep='\t', decimal='.', converters={0:self.parse_time}, encoding='cp1252', index_col = False)

        if self.parameters['filetype'] == 'rtd':
            df['azimuth_angle'] = df.Position
            df['elevation_angle'] = parameters['ScanAngle(°)']
            
        return df


    def create_variables(self, output_dataset):
        output_dataset.createDimension('range', len(self.parameters['Altitudes(m)']))
        output_dataset.createDimension('time', None)

        output_dataset.site = self.parameters['Localisation']

        # create the coordinate variables
        range1 = output_dataset.createVariable('range', 'f4', ('range',))
        range1.units = 'm'
        range1.long_name = 'range_gate_distance_from_lidar'
        range1[:] = np.array(self.parameters['Altitudes(m)'])


        time = output_dataset.createVariable('time', str, ('time',))
        time.units = 's'
        time.long_name = 'Time UTC in ISO 8601 format yyyy-mm-ddThh:mm:ssZ'            

        # create the beam steering and location variables
        yaw = output_dataset.createVariable('yaw', 'f4')
        yaw.units = 'degrees'
        yaw.long_name = 'lidar_yaw_angle'
        yaw[:] = self.parameters['DirectionOffset(°)']

        pitch = output_dataset.createVariable('pitch', 'f4')
        pitch.units = 'degrees'
        pitch.long_name = 'lidar_pitch_angle'
        pitch[:] = self.parameters['PitchAngle(°)']

        roll = output_dataset.createVariable('roll', 'f4')
        roll.units = 'degrees'
        roll.long_name = 'lidar_roll_angle'
        roll[:] = self.parameters['RollAngle(°)']

        # create the data variables
        scan_type = output_dataset.createVariable('scan_type', 'i')
        scan_type.units = 'none'
        scan_type.long_name = 'scan_type_of_the_measurement'
        scan_type[:] = 2

        accumulation_time = output_dataset.createVariable('accumulation_time', 'f4')
        accumulation_time.units = 'seconds'
        accumulation_time.long_name = 'time_for_spectral_accumulation'
        accumulation_time[:] = 1.0

        n_spectra = output_dataset.createVariable('n_spectra', 'f4')
        n_spectra.units = 'none'
        n_spectra.long_name = 'number_of_pulses'
        n_spectra[:] = self.parameters['NumberOfAveragedShots']

        # high resolution rtd files
        if self.parameters['filetype'] == 'rtd':
            VEL = output_dataset.createVariable('VEL', 'f4', ('time', 'range'))
            VEL.units = 'm.s-1'
            VEL.long_name = 'radial_velocity'
            
            azimuth_angle = output_dataset.createVariable('azimuth_angle', 'f4', ('time'))
            azimuth_angle.units = 'degrees'
            azimuth_angle.long_name = 'azimuth_angle_of_lidar_beam'

            elevation_angle = output_dataset.createVariable('elevation_angle', 'f4', ('time'))
            elevation_angle.units = 'degrees'
            elevation_angle.long_name = 'elevation_angle_of_lidar_beam'

            CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
            CNR.units = 'dB'
            CNR.long_name = 'carrier_to_noise_ratio'
            
            WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
            WIDTH.units = 'm.s-1'
            WIDTH.long_name = 'doppler_spectrum_width'
            
            T_internal = output_dataset.createVariable('T_internal', 'f4', ('time',))
            T_internal.units = 'degrees C'
            T_internal.long_name = 'internal_temperature'
            
            wiper_state = output_dataset.createVariable('wiper_state', str, ('time',))
            wiper_state.units = ''
            wiper_state.long_name = 'wiper_state'
        
        # 10 minute mean data sta files
        else:
            WS = output_dataset.createVariable('WS', 'f4', ('time', 'range'))
            WS.units = 'm.s-1'
            WS.long_name = 'mean_of_scalar_wind_speed'
            
            WSstd = output_dataset.createVariable('WSstd', 'f4', ('time', 'range'))
            WSstd.units = 'm.s-1'
            WSstd.long_name = 'standard_deviation_of_scalar_wind_speed'
            
            WSmax = output_dataset.createVariable('WSmax', 'f4', ('time', 'range'))
            WSmax.units = 'm.s-1'
            WSmax.long_name = 'maximum_of_scalar_wind_speed'
            
            WSmin = output_dataset.createVariable('WSmin', 'f4', ('time', 'range'))
            WSmin.units = 'm.s-1'
            WSmin.long_name = 'minimum_of_scalar_wind_speed'
            
            DIR = output_dataset.createVariable('DIR', 'f4', ('time', 'range'))
            DIR.units = 'degrees'
            DIR.long_name = 'mean_wind_direction'
            
            u = output_dataset.createVariable('u', 'f4', ('time', 'range'))
            u.units = 'm.s-1'
            u.long_name = 'mean_u_component_of_wind_speed'
            
            ustd = output_dataset.createVariable('ustd', 'f4', ('time', 'range'))
            ustd.units = 'm.s-1'
            ustd.long_name = 'standard_deviation_of_u_component_of_wind_speed'
            
            v = output_dataset.createVariable('v', 'f4', ('time', 'range'))
            v.units = 'm.s-1'
            v.long_name = 'mean_v_component_of_wind_speed'
            
            vstd = output_dataset.createVariable('vstd', 'f4', ('time', 'range'))
            vstd.units = 'm.s-1'
            vstd.long_name = 'standard_deviation_of_v_component_of_wind_speed'
            
            w = output_dataset.createVariable('w', 'f4', ('time', 'range'))
            w.units = 'm.s-1'
            w.long_name = 'mean_w_component_of_wind_speed'
            
            wstd = output_dataset.createVariable('wstd', 'f4', ('time', 'range'))
            wstd.units = 'm.s-1'
            wstd.long_name = 'standard_deviation_of_w_component_of_wind_speed'
            
            CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
            CNR.units = 'dB'
            CNR.long_name = 'mean_carrier_to_noise_ratio'
                        
            CNRstd = output_dataset.createVariable('CNRstd', 'f4', ('time', 'range'))
            CNRstd.units = 'dB'
            CNRstd.long_name = 'standard_deviation_of_carrier_to_noise_ratio'
            
            CNRmax = output_dataset.createVariable('CNRmax', 'f4', ('time', 'range'))
            CNRmax.units = 'dB'
            CNRmax.long_name = 'maximum_carrier_to_noise_ratio'
                        
            CNRmin = output_dataset.createVariable('CNRmin', 'f4', ('time', 'range'))
            CNRmin.units = 'dB'
            CNRmin.long_name = 'minimum_carrier_to_noise_ratio'
            
            WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
            WIDTH.units = 'm.s-1'
            WIDTH.long_name = 'mean_doppler_spectrum_width'
            
            WIDTHstd = output_dataset.createVariable('WIDTHstd', 'f4', ('time', 'range'))
            WIDTHstd.units = 'm.s-1'
            WIDTHstd.long_name = 'standard_deviation_of_doppler_spectrum_width'
            
            T_internal = output_dataset.createVariable('T_internal', 'f4', ('time',))
            T_internal.units = 'degrees C'
            T_internal.long_name = 'mean_internal_temperature'
            
            Availability = output_dataset.createVariable('Availability', 'f4', ('time','range'))
            Availability.units = 'percent'
            Availability.long_name = '10_minute_availability'
            
            wiper = output_dataset.createVariable('wiper', 'f4', ('time',))
            wiper.units = ''
            wiper.long_name = 'wiper_count'

    
    def write_file(self, output_dataset, df):
        output_dataset.variables['scan_type'][:] = 2
        output_dataset.variables['accumulation_time'][:] = 1.0
        
        if self.parameters['filetype'] == 'rtd': # high resolution data
            output_dataset.variables['time'][:] = df['Date'].values
            output_dataset.variables['T_internal'][:] = df['Temperature (°C)'].values
            output_dataset.variables['wiper_state'][:] = df['Wiper'].values
            output_dataset.variables['azimuth_angle'][:] = df['azimuth_angle'].values
            output_dataset.variables['elevation_angle'][:] = df['elevation_angle'].values
            output_dataset.variables['VEL'][:, :] = df.loc[:,['Vh-' in column for column in df.columns]]
            output_dataset.variables['WIDTH'][:, :] = df.loc[:,['RWS-' in column for column in df.columns]]
            output_dataset.variables['CNR'][:, :] = df.loc[:,['CNR-' in column for column in df.columns]]
            
			# filetype == 'sta' # 10 minute mean values
        else:
            output_dataset.variables['time'][:] = df['Date'].values
            output_dataset.variables['T_internal'][:] = df['Tm'].values
            output_dataset.variables['wiper'][:] = df['WiperCount'].values
            output_dataset.variables['WS'][:, :] = df.loc[:,['Vhm' in column for column in df.columns]]
            output_dataset.variables['WSstd'][:, :] = df.loc[:,['dVh' in column for column in df.columns]]
            output_dataset.variables['WSmin'][:, :] = df.loc[:,['VhMin' in column for column in df.columns]]
            output_dataset.variables['WSmax'][:, :] = df.loc[:,['VhMax' in column for column in df.columns]]
            output_dataset.variables['DIR'][:, :] = df.loc[:,['Azim' in column for column in df.columns]]
            output_dataset.variables['u'][:, :] = df.loc[:,['um' in column for column in df.columns]]
            output_dataset.variables['ustd'][:, :] = df.loc[:,['du' in column for column in df.columns]]
            output_dataset.variables['v'][:, :] = df.loc[:,['vm' in column for column in df.columns]]
            output_dataset.variables['vstd'][:, :] = df.loc[:,['dv' in column for column in df.columns]]
            output_dataset.variables['w'][:, :] = df.loc[:,['wm' in column for column in df.columns]]
            output_dataset.variables['wstd'][:, :] = df.loc[:,['dw' in column for column in df.columns]]
            output_dataset.variables['CNR'][:, :] = df.loc[:,[(('CNRm' in column) & ('CNRmax' not in column) & ('CNRmin' not in column) ) for column in df.columns]]
            output_dataset.variables['CNRstd'][:, :] = df.loc[:,['dCNR' in column for column in df.columns]]
            output_dataset.variables['CNRmax'][:, :] = df.loc[:,['CNRmax' in column for column in df.columns]]
            output_dataset.variables['CNRmin'][:, :] = df.loc[:,['CNRmin' in column for column in df.columns]]
            output_dataset.variables['WIDTH'][:, :] = df.loc[:,[(('spectral broedening' in column) & ('dspectral broedening' not in column)) for column in df.columns]]
            output_dataset.variables['WIDTHstd'][:, :] = df.loc[:,['dspectral broedening' in column for column in df.columns]]
            output_dataset.variables['Availability'][:, :] = df.loc[:,['Avail' in column for column in df.columns]]

    
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
                
                
if __name__ == '__main__':
    #debugging purposes
    import netCDF4 as nc
    file1 = r'C:\Users\skulla\Desktop\WLS7-71_2017_07_20__00_00_00.sta'
    test = Windcubev1()
    
    with nc.Dataset('test.nc', 'w', format='NETCDF4') as dataset:
        loaded_data = test.load_file(file1)
        test.read_to(dataset,file1,None,None)
