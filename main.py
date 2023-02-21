import os

import Metashape
import argparse
from glob import glob

from progress_recorder import ProgressRecorder


def get_photos(image_folder: str) -> list[str]:
    return (
            glob(f'{image_folder}/*.jpg')
            + glob(f'{image_folder}/*.png')
            + glob(f'{image_folder}/*.jpeg')
            + glob(f'{image_folder}/*.JPG')
            + glob(f'{image_folder}/*.PNG')
            + glob(f'{image_folder}/*.JPEG')
    )


def log_actions_and_save(action: str, doc: Metashape.Document) -> None:
    print('*' * 20, action, '*' * 20, sep='\n')
    doc.save()


def export_results(chunk, args: argparse.Namespace) -> None:
    if args.export_report:
        chunk.exportReport(args.output_dir + '/report.pdf')

    if args.export_model and chunk.model:
        chunk.exportModel(args.output_dir + '/model.obj')

    if args.export_point_cloud and chunk.point_cloud:
        chunk.exportPointCloud(args.output_dir + '/point_cloud.las', source_data=Metashape.PointCloudData)

    if args.export_dem and chunk.elevation:
        chunk.exportRaster(args.output_dir + '/dem.tif', source_data=Metashape.ElevationData)

    if args.export_orto and chunk.orthomosaic:
        if args.small_file:
            compression = Metashape.ImageCompression()
            compression.tiff_compression = Metashape.ImageCompression.TiffCompressionJPEG
            compression.jpeg_quality = 20
            chunk.exportRaster(args.output_dir + '/orthomosaic.tif', source_data=Metashape.OrthomosaicData,
                               image_compression=compression)
        else:
            chunk.exportRaster(args.output_dir + '/orthomosaic.tif', source_data=Metashape.OrthomosaicData,
                               progress=get_progress_of('Building raster'))


def get_progress_of(process: str):
    def get_progress_status(progress: float):
        progress_recorder.save_progress(process, progress)

    return get_progress_status


def main(args: argparse.Namespace) -> None:
    doc = Metashape.Document()
    doc.save(path=os.path.join('.', "project.psx"))
    doc.read_only = False

    chunk = doc.addChunk()
    chunk.addPhotos(get_photos(args.image_dir))

    log_actions_and_save(f'{len(chunk.cameras)} images imported, start matching them!', doc)

    chunk.matchPhotos(downscale=1, generic_preselection=True, reference_preselection=False, keypoint_limit=40000,
                      tiepoint_limit=10000, progress=get_progress_of('Matching photos'))

    log_actions_and_save(f'Start aligning photos', doc)
    chunk.alignCameras(adaptive_fitting=True, progress=get_progress_of('Aligning cameras'))

    log_actions_and_save(f'Start building depth map', doc)
    chunk.buildDepthMaps(downscale=4, filter_mode=Metashape.MildFiltering,
                         progress=get_progress_of('Building depth map'))

    log_actions_and_save(f'Start building model', doc)
    chunk.buildModel(source_data=Metashape.DepthMapsData, progress=get_progress_of('Building model'))

    if args.export_model:
        log_actions_and_save(f'Start building UV', doc)
        chunk.buildUV(page_count=2, texture_size=4096, progress=get_progress_of('Building UV'))

        log_actions_and_save(f'Start building textures', doc)
        chunk.buildTexture(texture_size=4096, ghosting_filter=True, progress=get_progress_of('Building textures'))

    log_actions_and_save(f'Start building point cloud', doc)
    chunk.buildPointCloud()

    log_actions_and_save(f'Start building digital elevation model', doc)
    chunk.buildDem(source_data=Metashape.PointCloudData, progress=get_progress_of('Building DEM'))

    log_actions_and_save(f'Start building orthomosaic', doc)
    chunk.buildOrthomosaic(progress=get_progress_of('Building orthomosaic'))

    log_actions_and_save(f'Start exporting', doc)
    export_results(chunk, args)


def set_parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser(description='Orthomosaic maker!')
    arg_parser.add_argument('--image_dir', type=str, help='Directory with input images.', default='images')
    arg_parser.add_argument('--output_dir', type=str, help='Directory with input images.', default='results')
    arg_parser.add_argument('--small_file', type=bool, help='Compress highly', default=False)
    arg_parser.add_argument('--export_orto', type=bool, help='Export orthomosaic', default=True)
    arg_parser.add_argument('--export_report', type=bool, help='Export general report', default=False)
    arg_parser.add_argument('--export_model', type=bool, help='Export model', default=False)
    arg_parser.add_argument('--export_point_cloud', type=bool, help='Export point cloud', default=False)
    arg_parser.add_argument('--export_dem', type=bool, help='Export DEM', default=False)
    arg_parser.add_argument('--flight_id', type=str, help='Flight ID at MongoDB', default=None)

    return arg_parser


if __name__ == '__main__':
    parser = set_parser()
    args = parser.parse_args()

    progress_recorder = ProgressRecorder(5, args.flight_id)

    main(args)
