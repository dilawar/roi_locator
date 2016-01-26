#!/usr/bin/env python

"""df_by_f_plotter_50.py

Plot df_by_f with 50% max thresholding.


"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

from image_analysis import frame_reader as fr
import cv2
import numpy as np
import pylab
import os
import glob
import scipy.stats as stats

def normalize( vec ):
    # normalize to (0, 1)
    a, b = vec.min(), vec.max()
    if (b - a) == 0:
        return np.zeros( len(vec) )
    elif (b - a) / b < 1e-2:
        print('[WARN] This roi does not show much activity. Ignoring')
        return np.zeros( len(vec) )
    scaled = (vec)/(b-a) - (a/(b-a))
    return scaled


def df_by_f( vec ):
    baseline = np.median(vec[0:49])
    if baseline > 0.0:
        # vec = stats.threshold(vec, baseline, vec.max())
        vec = ( vec - baseline ) / baseline
    return vec # normalize( vec )
    
def get_rois( roifile ):
    print('[INFO] Reading rois from %s' % roifile)
    rois = np.genfromtxt(roifile, delimiter=',', comments='#', skip_header=True)
    rois_ = []
    for r in rois:
        rois_.append( list(r) )
    rois = sorted(rois_, key = lambda x: x[1])
    return rois

def compute_df_by_f( roi, frames ):
    """Compute df/f for given ROI in each frame and return the array """
    col, row, r = roi
    p1, p2 = (row-r, col-r), (row+r, col+r) 
    mask = np.zeros( shape = frames[0].shape )
    # Holder to create image with given df/f ratio
    img = np.zeros( shape = mask.shape )
    dfbyf = np.zeros( len(frames) )
    for i, f in enumerate(frames):
        # Draw a filled circle on mask
        cv2.circle( mask, (int(row), int(col)), int(r), 1, -1) # Filled circle -1
        img[ mask == 1 ] = f[ mask == 1 ]
        #cv2.imshow( 'mask', img )
        dfbyf[i] =  img.mean() 
    #cv2.waitKey( 0 )
    dfbyf = df_by_f( dfbyf )
    return dfbyf

def threshold( dfbyfimg ):
    new_rows = []
    for r in dfbyfimg:
        thres = r.max() / 2.0
        r = r - thres
        rr = np.clip( r, 0, r.max())
        new_rows.append( rr )
    return np.array(new_rows)

def main( input_path, roi_file, outfile = None):
    global img_
    rois = get_rois( roi_file )

    # For this roi, there could be multiple files
    if os.path.isdir( input_path ):
        imagefiles = glob.glob( os.path.join( input_path, '*.tif') )
        imagefiles += glob.glob( os.path.join( input_path, '*.tiff' ) )
    else:
        imagefiles = [ input_path ]

    alldfbyfImg = []
    for imagefile in imagefiles:
        print('[INFO] Computing df/f for %s' % imagefile)
        dfbyfImg = process_image_file( rois, imagefile, outfile)
        alldfbyfImg.append( dfbyfImg )

    dfbyfMean = np.mean(alldfbyfImg, axis=0)
    dfbyfMean = threshold( dfbyfMean )

    outfile = '%s_dfbyf_avg_%s.dat' % (outfile or imagefile, len(imagefiles) )
    np.savetxt( outfile, dfbyfMean, delimiter=',' )
    print('[INFO] Writing dfbyf data to %s' % outfile)
    xmin, xmax = 0, dfbyfMean.shape[1] / args.frame_rate
    ymin, ymax = 0, dfbyfMean.shape[0]
    cx = pylab.imshow( dfbyfMean, cmap = pylab.cm.hot, aspect = 'auto'
            , extent = (xmin, xmax, ymax, ymin)
            , interpolation = 'none'
            )
    pylab.xticks( np.arange( xmin, xmax, 1.0) )
    pylab.colorbar( cx , orientation = 'horizontal' )

    pylab.title = 'df/f in ROIs'
    pylab.xlabel( 'Time (sec) ')
    pylab.ylabel( '# roi ')
    outfile = '%s_df_by_f_avg_%s.png' % ( outfile or imagefile, len(imagefiles))
    pylab.savefig( outfile )
    print('[INFO] Done saving datafile to %s ' % outfile)


def process_image_file( rois, imagefile, outfile):

    frames = fr.read_frames( imagefile )
    img_ = np.zeros( frames[0].shape )

    # This image keep one row for each df/f, and one column for each frame 
    dfbyfImg = np.zeros( shape = ( len(rois), len(frames) ) )
    for i, roi in enumerate(rois):
        vec = np.array(compute_df_by_f( roi, frames ))
        dfbyfImg[i,:] = vec
    return dfbyfImg

if __name__ == '__main__':
    import argparse
    # Argument parser.
    description = '''Locate ROI's manually'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--input', '-i'
        , required = True
        , help = 'Input file or directory (tif file are supported.)'
        )
    parser.add_argument('--roifile', '-r'
        , required = True
        , help = 'ROI file (csv)'
        )
    parser.add_argument( '--debug', '-d'
        , required = False
        , default = 0
        , type = int
        , help = 'Enable debug mode. Default 0, debug level'
        )
    parser.add_argument('--outfile', '-o'
        , required = False
        , help = 'Output file path'
        )
    parser.add_argument('--frame_rate', '-fr'
        , required = False
        , default = 10.0
        , type = float
        , help = 'Frame per second'
        )
    class Args: pass 
    args = Args()
    parser.parse_args(namespace=args)
    main( args.input, args.roifile, args.outfile)