import json
import sys
from rios import fileinfo
from rios import applier
from datetime import datetime
from makerobustmodel import RobustModel
import numpy as np

def gen_band_masks(info, inputs, outputs, other_args):
    
    """Run per-block by RIOS. In this case each block is a 
    single pixel. Given a block of values for each band for each date, returns
    a numpy array containing a mask where screened out data = 1 and data
    to keep = 0."""
    
    dates = other_args.dates
    nodata = other_args.nodata
    num_bands = other_args.num_bands
    thresh = other_args.threshold

    # Set up default output
    # Assumes all pixels are clear
    # Remember this is output for a single pixel through time
    results = np.zeros((len(inputs.images), num_bands, 1, 1), dtype='int16')

    all_band_data = np.array(dates)
    
    # Get data for one band at a time
    for b in range(0, num_bands):
        
        band_data = np.array([[inputs.images[t][b][0][0]] for t in range(0, len(inputs.images))])
      
        all_band_data = np.hstack((all_band_data, band_data))
        
    drop_indices = np.where(np.any(all_band_data == nodata, axis=1))

    drop_indices = np.array(drop_indices).reshape(-1)

    # Remove any rows where all band values are 0
    all_band_data =  all_band_data[np.all(all_band_data != nodata, axis=1)]
    
    # Need a minimum of 12 observations
    if(len(all_band_data) >= 12):
        
        num_years = np.ceil((np.max(dates) - np.min(dates)) / 365)
               
        # Output array needs to be matched in size to input array
        output_arr = np.delete(results, drop_indices, axis=0)
        
        try:
        
            for i in range(1, num_bands+1):
                
                # Create model object
                rm = RobustModel(all_band_data[:,0], num_years)
                
                # Get data for this band
                bd = all_band_data[:,i]
                
                # Fit the robust model
                rm.fitModel(bd)
                
                # Find low outliers
                too_low = np.where(rm.residuals < -rm.RMSE*thresh)
                
                output_arr[too_low, i-1] = -1
                
                # Find high outliers
                too_high = np.where(rm.residuals > rm.RMSE*thresh)
                
                output_arr[too_high, i-1] = 1
                  
            results = np.insert(output_arr, drop_indices, np.zeros((len(drop_indices), num_bands, 1, 1)), axis=0)  
            
        except np.linalg.LinAlgError as e:
            print("Warning: {}".format(e))
            pass
    
    curr_percent = float(info.yblock * info.xtotalblocks + info.xblock) / float(info.xtotalblocks * info.ytotalblocks) * 100
    print('{:.2f}'.format(curr_percent))
    
    outputs.outimage = results   

def get_ST_masks(json_fp, bands=None, output_driver='KEA', num_processes=1, threshold=3):
    
    """Main function to run to generate the output masks. Given an input JSON file, 
    generates a mask for each date, for each band where 0=Inlier, 1=High outlier, 
    -1=Low outlier. Opening/closing of files, generation of blocks and use of 
    multiprocessing is all handled by RIOS.
    
    A minimum of 12 observations is required to create the masks.
    
    
    json_fp:       Path to JSON file which provides a dictionary where for each
                   date, an input file name and an output file name are provided.
    output_driver: Short driver name for GDAL, e.g. KEA, GTiff.
    num_processes: Number of concurrent processes to use.
    bands:         List of GDAL band numbers to use, e.g. [1, 3, 5]. Defaults to all.
    threshold:     Threshold for screening. Defaults to 3, meaning that observations
                   outside 3*RMSE of the fitted model will be counted as outliers.
                   Lower values will result in more outliers being detected.
    """
    
    ip_paths = []
    op_paths = []
    dates = []
    
    try:
        # Open and read JSON file containing date:filepath pairs
        with open(json_fp) as json_file:  
            image_list = json.load(json_file)
        
            for date in image_list.items():
                dates.append([datetime.strptime(date[0], '%Y-%m-%d').toordinal()])
                ip_paths.append(date[1]['input'])
                op_paths.append(date[1]['output'])
    except FileNotFoundError:
        print('Could not find the provided JSON file.')
        sys.exit()
    except json.decoder.JSONDecodeError as e:
        print('There is an error in the provided JSON file: {}'.format(e))
        sys.exit()
        
    # Create object to hold input files    
    infiles = applier.FilenameAssociations()
    infiles.images = ip_paths
    
    # Create object to hold output file
    outfiles = applier.FilenameAssociations()
    outfiles.outimage = op_paths
    
    # ApplierControls object holds details on how processing should be done
    app = applier.ApplierControls()
    
    # Set window size to 1 because we are working per-pixel
    app.setWindowXsize(1)
    app.setWindowYsize(1)
    
    # Set output file type
    app.setOutputDriverName(output_driver)
    
    # Use Python's multiprocessing module
    app.setJobManagerType('multiprocessing')
    app.setNumThreads(num_processes)
    
    # Open first image in list to use as a template
    template_image = fileinfo.ImageInfo(infiles.images[0])
    
    # Get no data value
    nodata = template_image.nodataval[0]
    
    if not bands: # No bands specified - default to all
        
        num_bands = template_image.rasterCount
        bands = [i for i in range(1, num_bands+1)]
    
    else: # If a list of bands is provided
    
        # Number of bands determines things like the size of the output array
        num_bands = len(bands)
    
        # Need to tell the applier to only use the specified bands 
        app.selectInputImageLayers(bands)
    
    full_names = [template_image.layerNameFromNumber(i) for i in bands]    
    
    # Set up output layer name
    app.setLayerNames(full_names)
    
    # Additional arguments - have to be passed as a single object
    other_args = applier.OtherInputs()
    other_args.dates = dates
    other_args.threshold = threshold
    other_args.nodata = nodata
    other_args.num_bands = num_bands
    
    template_image = None
    
    try:
        applier.apply(gen_band_masks, infiles, outfiles, otherArgs=other_args, controls=app)
    except RuntimeError as e:
        print('There was an error processing the images: {}'.format(e))
        print('Do all images in the JSON file exist?')

# Example
get_ST_masks('example.json', bands=[2, 3, 4, 5, 6], num_processes=8)















