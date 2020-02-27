This repository contains a set of functions which allow you to use RIOS (http://www.rioshome.org/) to process a stack of raster images into a set of outlier masks. To find the outliers, a robust season-trend model is fitted to the time series for each band for each pixel, and the RMSE of the model is calculated. Values outside of a specific multiple of the RMSE (user settable; defaults to 3) are masked. The output is a set of *d* rasters, each with *n* bands, where *d* is the number of dates and *n* is the number of input bands selected (GDAL band numbering). In each layer, 0 indicates no outlier detected, -1 indicates a low outlier, and 1 indicates a high outlier.

Relevant papers:

Roerink, G. J., Menenti, M., and Verhoef, W. Reconstructing cloudfree NDVI composites using Fourier analysis of time series. *International Journal of Remote Sensing*. **2000**, *21*, 1911-1917. doi:10.1080/014311600209814.

Zhu, Z. and Woodcock, C.E. Automated cloud, cloud shadow, and snow detection in multitemporal Landsat data: An algorithm designed specifically for monitoring land cover change. *Remote Sensing of Environment.* **2014**, *152*, 217–234. doi:10.1016/j.rse.2014.06.012.

Zhu, Z.; Woodcock, C.E.; Holden, C.; Yang, Z. Generating synthetic Landsat images based on all available Landsat data: Predicting Landsat surface reflectance at any given time. *Remote Sensing of Environment*. **2015**, *162*, 67–83. doi:10.1016/j.rse.2015.02.009.


