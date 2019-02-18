import numpy as np
from ..core import Reader
from datetime import datetime
import pandas as pd
import re
from pathlib import Path

class ZephIR300(Reader):

    def __init__(self):
        super().__init__(False)

    def accepts_file(self, filename):
        return (filename.endswith(('.csv','.CSV')) & filename.startswith('Wind'))

    def output_filename(self, filename):
        return filename[:-4]

    def parse_time(self, string1):
            try:
                temp = datetime.strptime(string1,'%d.%m.%Y %H:%M:%S')
            except:
                try:
                    temp = datetime.strptime(string1,'%d/%m/%Y %H:%M:%S')
                except:
                    temp = datetime.strptime(string1,'%d.%m.%Y %H:%M')
            temp = temp.isoformat() +'Z'
            return temp


    @staticmethod
    def get_timestamp(input_filepath, row_of_timestamp = 0 ):
        with open(input_filepath) as f:
            line = f.readlines()[2 + row_of_timestamp]
            

        timestamp = datetime.strptime(line.split(';')[1], 
                                          '%d.%m.%Y %H:%M:%S')
            
        return timestamp

    def check_version(self, input_filepath):
        ten_min_file = (re.findall(r'(?<=\\)\w+(?=_\d+@)',input_filepath)[0] == r'Wind10')
        version_number = re.findall(r'(?<=Wind\d._)\d+(?=@Y)',input_filepath)[0]
        return ten_min_file, version_number
    
    def load_file(self, input_filepath):
        with open(input_filepath,'r', encoding='latin-1') as f:
                header = f.readline()
                
                #check for most common character -> column seperator
                count_comma = sum(character == ',' for character in header)
                count_semicolon = sum(character == ';' for character in header)
                
                if count_comma > count_semicolon:
                    seperator = ','
                    decimal = '.'
                else:
                    seperator = ';'
                    decimal = ','
                
                #get parameters from header
                header = header.split(seperator)
                parameters = {line.split(':')[0].strip(): line.split(':')[1].strip() for line in header if ':' in line}
                parameters['Measurement heights'] = [int(element.strip()) for element in parameters['Measurement heights'].split('m') if (element != '')]
                parameters['Measurement heights'].append(1)

        #load file into DataFrame
        df = pd.read_csv(input_filepath, sep = seperator, skiprows = 1, decimal = decimal) 
        df['timestamp_iso8601'] = df['Time and Date'].apply(self.parse_time)

        return df, parameters
        
                
    def create_variables(self, output_dataset, df, parameters, ten_min_file):
        output_dataset.createDimension('range', len(parameters['Measurement heights']))
        output_dataset.createDimension('time', None)

        # create the coordinate variables
        range1 = output_dataset.createVariable('range', 'f4', ('range',))
        range1.units = 'm'
        range1.long_name = 'range_gate_distance_from_lidar'
        range1[:] = np.array(parameters['Measurement heights'])

        time = output_dataset.createVariable('time', str, ('time',))
        time.units = 's'
        time.long_name = 'timestamp ISO 8601'

        # create the data variables
        scan_type = output_dataset.createVariable('scan_type', 'i')
        scan_type.units = 'none'
        scan_type.long_name = 'scan_type_of_the_measurement'
        scan_type[:] = 1

        accumulation_time = output_dataset.createVariable('accumulation_time', 'f4')
        accumulation_time.units = 'seconds'
        accumulation_time.long_name = 'time_for_spectral_accumulation'
        accumulation_time[:] = 1.0

        # create the measurement variables
        
        # Beschreibung einfügen
        tilt = output_dataset.createVariable('tilt', 'f4', ('time',))
        tilt.units = 'degrees north'
        tilt.long_name = 'either pitch or roll depending on higher value'

        T_external = output_dataset.createVariable('T_external', 'f4', ('time',))
        T_external.units = 'degrees C'
        T_external.long_name = 'temperature'

        yaw = output_dataset.createVariable('yaw', 'f4', ('time',))
        yaw.units = 'degrees'
        yaw.long_name = 'lidar_yaw_angle'

        rh = output_dataset.createVariable('rh', 'f4', ('time',))
        rh.units = 'degrees'
        rh.long_name = 'lidar_yaw_angle'
        
        p = output_dataset.createVariable('p', 'f4', ('time',))
        p.units = 'degrees'
        p.long_name = 'lidar_yaw_angle'

        WS = output_dataset.createVariable('WS', 'f4', ('time', 'range'))
        WS.units = 'm.s-1'
        WS.long_name = 'mean of scalar wind speed'
        
        DIR = output_dataset.createVariable('DIR', 'f4', ('time', 'range'))
        DIR.units = 'degrees north'
        DIR.long_name = 'wind direction from north'
        
        if ten_min_file:
            n_valid = output_dataset.createVariable('n_valid', 'f4', ('time', 'range'))
            n_valid.units = '-'
            n_valid.long_name = 'number of valid scans in averaging period'

            if 'Proportion Of Packets With Rain (%)' in df.columns:
                proportion_of_rain = output_dataset.createVariable('proportion_of_rain', 'f4', ('time',))
                proportion_of_rain.units = 'percent'
                proportion_of_rain.long_name = 'Proportion Of Packets With Rain'
            elif 'Raining' in df.columns:
                proportion_of_rain = output_dataset.createVariable('rain', 'f4', ('time',))
                proportion_of_rain.units = 'boolean'
                proportion_of_rain.long_name = 'indictor for rain; 1 is rain 0 no rain'

            if 'Lower Temp. (C)' in df.columns:
                TMin = output_dataset.createVariable('T_min', 'f4', ('time',))
                TMin.units = 'degrees C'
                TMin.long_name = 'min of temperature'
                
            if 'Upper Temp. (C)' in df.columns:
                TMax = output_dataset.createVariable('T_max', 'f4', ('time',))
                TMax.units = 'degrees C'
                TMax.long_name = 'max of temperature'
                
            if any(('Horizontal Wind Speed Min' in column) for column in df.columns):
                WSMin = output_dataset.createVariable('WS_min', 'f4', ('time', 'range'))
                WSMin.units = 'm.s-1'
                WSMin.long_name = 'min of scalar wind speed'
                
            if any(('Horizontal Wind Speed Max' in column) for column in df.columns):
                WSMax = output_dataset.createVariable('WS_max', 'f4', ('time', 'range'))
                WSMax.units = 'm.s-1'
                WSMax.long_name = 'max of scalar wind speed'
                
            if any(('Horizontal Wind Speed Std. Dev.' in column) for column in df.columns):
                WSStd = output_dataset.createVariable('WS_std', 'f4', ('time', 'range'))
                WSStd.units = 'm.s-1'
                WSStd.long_name = 'std of scalar wind speed'
                
                
    def write_file(self, output_dataset, df, ten_min_file):
        met_ws_list = df['MET Wind Speed (m/s)']
        bool_ws = ['Horizontal Wind Speed (m/s) at' in column for column in df.columns]
        ws_list = df.loc[:,bool_ws]
        ws_list_complete = pd.concat([ws_list, met_ws_list],join='inner',axis=1)
        
        met_dir_list = df['MET Direction (deg)']
        bool_dir = ['Wind Direction (deg) at' in column for column in df.columns]
        dir_list = df.loc[:,bool_dir]
        dir_list_complete = pd.concat([dir_list, met_dir_list],join='inner',axis=1)
        
        output_dataset.variables['WS'][:, :] = ws_list_complete.values
        output_dataset.variables['DIR'][:, :] = dir_list_complete.values
        output_dataset.variables['time'][:] = df['timestamp_iso8601'].values        
        output_dataset.variables['T_external'][:] = df['Air Temp. (C)'].values        
        output_dataset.variables['tilt'][:] = df['Tilt (deg)'].values
        output_dataset.variables['yaw'][:] = df['ZephIR Bearing (deg)'].values
        output_dataset.variables['rh'][:] = df['Humidity (%)'].values
        output_dataset.variables['p'][:] = df['Pressure (mbar)'].values
        
        if ten_min_file:
            if 'Lower Temp. (C)' in df.columns:
                output_dataset.variables['T_min'][:] = df['Lower Temp. (C)'].values
            if 'Upper Temp. (C)' in df.columns:
                output_dataset.variables['T_max'][:] = df['Upper Temp. (C)'].values
            if 'Proportion Of Packets With Rain (%)' in df.columns:
                output_dataset.variables['proportion_of_rain'][:] = df['Proportion Of Packets With Rain (%)'].values
            elif 'Raining' in df.columns:
                output_dataset.variables['rain'][:] = df['Raining'].values
            
            bool_n_valid = ['Packets in Average at' in column for column in df.columns]
            n_valid_series = df.loc[:,bool_n_valid]
            n_valid_complete = pd.concat([n_valid_series,pd.Series(np.full_like(met_ws_list, np.nan),name='Packets in Average at MET')],join='inner',axis=1)
            output_dataset.variables['n_valid'][:, :] = n_valid_complete.values
            
            bool_WSMin = ['Horizontal Wind Speed Min' in column for column in df.columns]
            if any(bool_WSMin):
                WSMin_list = df.loc[:,bool_WSMin]
                WSMin_list_complete = pd.concat([WSMin_list, pd.Series(np.full_like(met_ws_list, np.nan))],join='inner',axis=1)
                output_dataset.variables['WS_min'][:] = WSMin_list_complete.values
        
            bool_WSMax = ['Horizontal Wind Speed Max' in column for column in df.columns]
            if any(bool_WSMax):
                WSMax_list = df.loc[:,bool_WSMax]
                WSMax_list_complete = pd.concat([WSMax_list, pd.Series(np.full_like(met_ws_list, np.nan))],join='inner',axis=1)
                output_dataset.variables['WS_max'][:] = WSMax_list_complete.values
                
            bool_WSStd = ['Horizontal Wind Speed Std. Dev.' in column for column in df.columns]
            if any(bool_WSStd):
                WSStd_list = df.loc[:,bool_WSStd]
                WSStd_list_complete = pd.concat([WSStd_list, pd.Series(np.full_like(met_ws_list, np.nan))],join='inner',axis=1)
                output_dataset.variables['WS_std'][:] = WSStd_list_complete.values


    def read_to(self, output_dataset, input_filepath, configs, appending):
        try:
            ten_min_file, version_number = self.check_version(input_filepath)
            df, parameters = self.load_file(input_filepath)
            self.create_variables(output_dataset, df, parameters, ten_min_file)
            self.write_file(output_dataset, df, ten_min_file)
            
        except Exception as err:
                print('Error ocurred while converting %s. See error.log for details.' % input_filepath)
                print(err)
                with open(Path(output_dataset.filepath()).parent / 'error.log','a') as logfile:
                    logfile.write( '%s'%output_dataset.filepath() +'\n')




