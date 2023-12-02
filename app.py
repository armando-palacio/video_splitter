import flet as ft
import os, shutil
import re
from moviepy.video.io.ffmpeg_reader import ffmpeg_parse_infos
import moviepy.editor as mp
import numpy as np
from pytube import YouTube
from flet import (Page, ElevatedButton, TextField, Row, Column, Icon, Image, IconButton, Checkbox, Tabs, Tab,
                  FilePicker, Text, Dropdown, icons, Checkbox, ProgressRing, UserControl, FilePickerResultEvent,
                  FloatingActionButton, Container)

VERSION = '1.1.0'

def delete_directory_contents(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

class Video_from_PC(UserControl):
    def __init__(self, page):
        super().__init__()
        self.FILE_PATH = '' 
        self.FILE_NAME = ''
        self.FILE_INFO = {}
        self.page = page
    
    def build(self):
        # Sección de carga de archivo (load)
        self.file_picker = FilePicker(on_result=self.load_file_callback)
        self.page.overlay.append(self.file_picker)
        self.load_file_button = ElevatedButton(
            'Load File', 
            icon=icons.FILE_UPLOAD, 
            on_click=lambda _: self.file_picker.pick_files(allow_multiple=False, allowed_extensions=['mp4','avi','mkv']),
            width = 140,
        )
        self.text_file_name = Text(color='orange')
        self.progress_ring = Row([ ProgressRing(width=25, height=25) ], visible=False)
        self.icon_load_ok = Row([ Icon(icons.CHECK, size=25, color='green')], visible=False)

        self.r_carga = Row([
            self.load_file_button, 
            self.text_file_name, 
            self.progress_ring, 
            self.icon_load_ok
        ])

        # Sección de información del archivo (info)
        self.resolucion = Text(color='orange')
        self.duracion = Text(color='orange')
        self.fps = Text(color='orange')

        self.c_info = Column([
            self.resolucion, 
            self.duracion, 
            self.fps], 
            
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Sección de selección de clips (split params)
        self.ti = TextField(label='T_init (s)', height=50, on_change=self.cotas_ti_callback, expand=1)
        self.dt = TextField(label='T_clips (s)', height=50, on_change=self.cotas_dt_callback, expand=1)
        self.r1 = Row([self.ti, self.dt], visible=False)

        self.tf = TextField(label='T_final (s)', height=50, on_change=self.cotas_tf_callback, expand=1)
        self.n_clips = TextField(label='# Clips', height=50, text_align='center', disabled=True, expand=1)
        self.r2 = Row([self.tf, self.n_clips], visible=False)

        self.out_field = TextField(label='Output Folder', height=50, disabled=True, expand=9, text_size=12, content_padding=10)
        self.check_out = Checkbox(on_change=self.check_out_callback, expand=1)
        self.r_out = Row([self.check_out, self.out_field], visible=False)

        self.split_button = ElevatedButton('Split', icon=ft.icons.CUT, on_click=self.split_callback, expand=1)
        self.cancel_button = ElevatedButton('Cancel', icon=ft.icons.CANCEL, on_click=self.cancel_callback, expand=1)
        self.r3 = Row([self.split_button, self.cancel_button], visible=False)

        self.c_clips = Column([
            self.r1, 
            self.r2,
            self.r_out, 
            self.r3,

        ], spacing=20, tight=True)

        # Sección de resultados (results)
        self.p_load = Row([ ProgressRing(width=25, height=25)], expand=1, visible=False)
        self.ch_load = Row([ Icon(icons.CHECK, size=25, color='green')], expand=1, visible=False)
        self.text_result_load = Text()

        self.p_proc = Row([ ProgressRing(width=25, height=25)], expand=1, visible=False)
        self.ch_proc = Row([ Icon(icons.CHECK, size=25, color='green')], expand=1, visible=False)
        self.text_result_proc = Text()

        self.p_save = Row([ ProgressRing(width=25, height=25)], expand=1, visible=False)
        self.ch_save = Row([ Icon(icons.CHECK, size=25, color='green')], expand=1, visible=False)
        self.text_result_save = Text()
        
        self.c_results = Column([
            Row([self.p_load, self.ch_load, Row([self.text_result_load], expand=9)]),
            Row([self.p_proc, self.ch_proc, Row([self.text_result_proc], expand=9)]),
            Row([self.p_save, self.ch_save, Row([self.text_result_save], expand=9)])
        ]) 

        self.whole = Container(
                content=Column([   
                self.r_carga,
                self.c_info,
                self.c_clips,
                self.c_results], 
                
                spacing=20, 
                tight=True
            ),
            padding=10
        )
        return self.whole

    def check_out_callback(self, e):
        if self.check_out.value:
            self.out_field.disabled = False
        else:
            self.out_field.disabled = True
        self.update()
    
    def load_file_callback(self, e: FilePickerResultEvent):
        if self.FILE_PATH != '' and self.FILE_NAME != '' and self.FILE_INFO != {}:
            self.clear_FILE_params()
            self.clear_results_sect()
            self.clear_load_sect()

        if e.files:
            self.progress_ring.visible = True
            self.update()

            self.FILE_PATH = e.files[0].path
            self.FILE_NAME = e.files[0].name
            self.FILE_INFO = ffmpeg_parse_infos(self.FILE_PATH)

            if self.FILE_INFO['video_rotation'] == 0:
                self.FILE_INFO['video_size'] = self.FILE_INFO['video_size'][::-1]

            self.text_file_name.value = self.FILE_NAME
            self.progress_ring.visible = False
            self.icon_load_ok.visible = True
            self.update()

            self.show_info_sect()
            self.show_split_params_sect()
            self.show_output_dir()

    def clear_FILE_params(self):
        self.FILE_PATH = ''
        self.FILE_NAME = ''
        self.FILE_INFO = {}

    def clear_load_sect(self):
        self.text_file_name.value = ''
        self.progress_ring.visible = False
        self.icon_load_ok.visible = False
        self.update()

    def clear_results_sect(self):
        self.text_result_load.value = ''
        self.text_result_proc.value = ''
        self.text_result_save.value = ''
        self.ch_load.visible = False
        self.ch_proc.visible = False
        self.ch_save.visible = False
        self.update()

    def show_info_sect(self):
        t = self.FILE_INFO["duration"]
        min, seg = divmod(t, 60)
        h = self.FILE_INFO["video_size"][0]
        w = self.FILE_INFO["video_size"][1]

        self.resolucion.value = f'Resolución: {h} x {w}'
        self.duracion.value = f'Duración: {t} s ({int(min)}:{int(seg)})'
        self.fps.value = f'FPS: {self.FILE_INFO["video_fps"]}'
        self.c_info.visible = True
        self.update()

    def show_output_dir(self):
        self.out_field.value = os.getcwd()
        self.r_out.visible = True
        self.update()
    
    def show_split_params_sect(self):
        t = self.FILE_INFO['duration']
        self.ti.value = '0.0'
        self.tf.value = t
        self.dt.value = min(30.0, t)
        self.r1.visible = True
        self.r2.visible = True
        self.r3.visible = True
        self.c_clips.visible = True
        self.update_clips_number()

    def cotas_ti_callback(self, e):
        if re.match(r'^[\d.,]+$', str(self.ti.value)):
            if float(self.ti.value) >= float(self.tf.value):
                self.ti.value = float(self.tf.value) - 1
            elif float(self.ti.value) < 0:
                self.ti.value = 0.0
        else:
            self.ti.value = 0.0
        self.cotas_dt_callback(self)

    def cotas_tf_callback(self, e):
        t = self.FILE_INFO['duration']
        if re.match(r'^[\d.,]+$', str(self.tf.value)):
            if float(self.tf.value) <= float(self.ti.value):
                self.tf.value = float(self.ti.value) + 1
            elif float(self.tf.value) > t:
                self.tf.value = t
        else:
            self.tf.value = t
        self.cotas_dt_callback(self)

    def cotas_dt_callback(self, e):
        if re.match(r'^[\d.,]+$', str(self.dt.value)):
            if float(self.dt.value) < 1:
                self.dt.value = 1.0
            if float(self.dt.value) > float(self.tf.value)-float(self.ti.value):
                self.dt.value = float(self.tf.value)-float(self.ti.value)
        else:
            self.dt.value = 30.0
        self.update_clips_number()

    def update_clips_number(self):
        if (float(self.tf.value) - float(self.ti.value))%float(self.dt.value) == 0:
            self.n_clips.value = int((float(self.tf.value) - float(self.ti.value))//float(self.dt.value))
        else:
            self.n_clips.value = int((float(self.tf.value) - float(self.ti.value))//float(self.dt.value)) + 1
        self.update()

    def cancel_callback(self, e):
        self.clear_FILE_params()
        self.clear_results_sect()
        self.clear_load_sect()
        self.c_info.visible = False
        self.c_clips.visible = False
        self.update()

    def split_callback(self, e):
        dir_name, extension = os.path.splitext(self.FILE_NAME)
        in_path = self.FILE_PATH
        out_path = os.path.join(self.out_field.value, dir_name)
        res = self.FILE_INFO['video_size']

        if not os.path.exists(out_path):
            os.mkdir(out_path)
        else:
            delete_directory_contents(out_path)
        
        self.clear_results_sect()
        
        t_end = float(self.tf.value)
        t_start = float(self.ti.value)
        clip_duration = float(self.dt.value)

        self.page.splash = ft.ProgressBar()
        self.whole.disabled = True
        self.update()

        self.text_result_load.value = 'Cargando el video...'
        self.p_load.visible = True
        self.page.update()

        with mp.VideoFileClip(in_path, target_resolution = res).subclip(t_start, t_end) as clip:
            self.p_load.visible = False
            self.ch_load.visible = True
            self.update()

            n = int((t_end - t_start)//clip_duration)
            rest_time = (t_end - t_start)%clip_duration

            self.text_result_proc.value = 'Procesando el video...'
            self.p_proc.visible = True
            self.update()

            clips = [clip.subclip(clip_duration*i, clip_duration*(i+1)) for i in np.arange(n)]; 
            if rest_time != 0: clips.append(clip.subclip(n*clip_duration, t_end-t_start))
            
            self.p_proc.visible = False
            self.ch_proc.visible = True
            self.update()

            self.text_result_save.value = 'Guardando los clips...'
            self.p_save.visible = True
            self.update()

            for i in np.arange(n):
                clips[i].write_videofile('{}/{}{}'.format(out_path, i+1, extension))
            if rest_time != 0: clips[n].write_videofile('{}/{}{}'.format(out_path, n+1, extension))

            self.p_save.visible = False
            self.ch_save.visible = True
            self.update()
        
        self.whole.disabled = False
        self.update()

        self.page.splash = None
        self.page.update()










class Video_from_YT(UserControl):
    def __init__(self, page):
        super().__init__()
        self.FILE_PATH = '' 
        self.FILE_NAME = ''
        self.FILE_INFO = {}
        self.page = page
        self.resolution_map = {
            "144p": (256, 144),
            "240p": (426, 240),
            "360p": (640, 360),
            "480p": (854, 480),
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "1440p": (2560, 1440),
            "2160p": (3840, 2160),
        }
        self.is_vertical = False
        self.streams = []
    
    def build(self):
        # Sección de carga de archivo
        self.url_field = TextField(hint_text='URL del video de Youtube..', height=50, on_submit=self.show_info_sect, on_change=self.show_download_button, visible=True, expand=5)
        self.download_button = IconButton(icon=icons.DOWNLOAD, on_click=self.show_info_sect, visible=True, expand=1)

        self.load_progress = Row([ ProgressRing(width=25, height=25)], expand=1, visible=False)
        self.load_ok = Row([ Icon(icons.CHECK, color='green', size=25)], expand=1, visible=False)

        self.r_carga = Row([
            self.url_field, 
            self.download_button, 
            self.load_progress, 
            self.load_ok
        ])

        # Sección de información del archivo
        self.res_dropdown = Dropdown(label='Resolución', width=150, color='orange', on_change=self.res_callback, expand=1)
        self.bytes = Text(color='orange', text_align=ft.TextAlign.CENTER, selectable=True)
        self.duration = Text(color='orange', text_align=ft.TextAlign.CENTER, selectable=True)
        self.img = Image(fit=ft.ImageFit.CONTAIN, expand=1)
        self.video_title = Text(width=250, color='orange', text_align=ft.TextAlign.CENTER, selectable=True)

        self.c_info = Column([
            Row([
                self.res_dropdown,
                Column([self.duration, self.bytes], alignment=ft.MainAxisAlignment.CENTER, expand=1)
            ]),

            Row([
                self.img, 
                Row([self.video_title], expand=2)
            ]),], 

            spacing=10, 
            tight=True, 
            visible=False
        )

        # Sección de selección de clips
        self.ti = TextField(label='T_init (s)', height=50, on_change=self.cotas_ti_callback, expand=1)
        self.dt = TextField(label='T_clips (s)', height=50, on_change=self.cotas_dt_callback, expand=1)
        self.r1 = Row([self.ti, self.dt])

        self.tf = TextField(label='T_final (s)', height=50, on_change=self.cotas_tf_callback, expand=1)
        self.n_clips = TextField(label='# Clips', height=50, text_align='center', disabled=True, expand=1)
        self.r2 = Row([self.tf, self.n_clips])

        self.out_field = TextField(label='Output Folder', height=50, disabled=True, expand=9, text_size=12, content_padding=10)
        self.check_out = Checkbox(on_change=self.check_out_callback, expand=1)
        self.r_out = Row([self.check_out, self.out_field])

        self.split_button = ElevatedButton('Split', icon=ft.icons.CUT, on_click=self.split_callback, expand=1)
        self.cancel_button = ElevatedButton('Cancel', icon=ft.icons.CANCEL, on_click=self.cancel_callback, expand=1)
        self.is_vertical_checkbox = Checkbox(label='Vertical', value = self.is_vertical, on_change=self.is_vertical_callback, expand=1)
        self.r3 = Row([self.split_button, self.cancel_button, self.is_vertical_checkbox])

        self.c_clips = Column([
            self.r1, 
            self.r2,
            self.r_out, 
            self.r3],
             
            spacing=20, 
            tight=True, 
            visible=False
        )

        # Sección de resultados
        self.p_download = Row([ ProgressRing(width=25, height=25)], expand=1, visible=False)
        self.ch_download = Row([ Icon(icons.CHECK, size=25, color='green')], expand=1, visible=False)
        self.text_result_download = Text()

        self.p_load = Row([ ProgressRing(width=25, height=25)], expand=1, visible=False)
        self.ch_load = Row([ Icon(icons.CHECK, size=25, color='green')], expand=1, visible=False)
        self.text_result_load = Text()

        self.p_proc = Row([ ProgressRing(width=25, height=25)], expand=1, visible=False)
        self.ch_proc = Row([ Icon(icons.CHECK, size=25, color='green')], expand=1, visible=False)
        self.text_result_proc = Text()

        self.p_save = Row([ ProgressRing(width=25, height=25)], expand=1, visible=False)
        self.ch_save = Row([ Icon(icons.CHECK, size=25, color='green')], expand=1, visible=False)
        self.text_result_save = Text()
        
        self.c_results = Column([
            Row([self.p_download, self.ch_download, Row([self.text_result_download], expand=9)], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            Row([self.p_load, self.ch_load, Row([self.text_result_load], expand=9)], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            Row([self.p_proc, self.ch_proc, Row([self.text_result_proc], expand=9)], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            Row([self.p_save, self.ch_save, Row([self.text_result_save], expand=9)], alignment=ft.MainAxisAlignment.SPACE_AROUND)], 
            
            spacing=10,
        )

        self.whole = Container(
            content=Column([   
                self.r_carga,
                self.c_info,
                self.c_clips,
                self.c_results], 
                
                spacing=20,
            ),
            padding=10,
        )
        return self.whole

    def check_out_callback(self, e):
        if self.check_out.value:
            self.out_field.disabled = False
        else:
            self.out_field.disabled = True
        self.update()

    def show_output_dir(self):
        self.out_field.value = os.getcwd()
        self.update()

    def clear_FILE_params(self):
        self.FILE_PATH = ''
        self.FILE_NAME = ''
        self.FILE_INFO = {}

    def clear_load_sect(self):
        self.url_field.value = ''
        self.load_ok.visible = False
        self.download_button.visible = True
        self.update()

    def clear_for_resplit(self):
        self.text_result_download.value = ''
        self.text_result_load.value = ''
        self.text_result_proc.value = ''
        self.text_result_save.value = ''
        self.ch_download.visible = False
        self.ch_load.visible = False
        self.ch_proc.visible = False
        self.ch_save.visible = False
        self.update()

    def cancel_callback(self, e):
        self.clear_FILE_params()
        self.clear_for_resplit()
        self.clear_load_sect()
        self.c_info.visible = False
        self.c_clips.visible = False
        self.c_results.visible = False
        self.update()

    def is_vertical_callback(self, e):
        self.is_vertical = self.is_vertical_checkbox.value
        self.FILE_INFO['video_size'] = self.FILE_INFO['video_size'][::-1]
    
    def res_callback(self, e):
        if self.is_vertical:
            self.FILE_INFO['video_size'] = self.resolution_map[self.res_dropdown.value]
        else:
            self.FILE_INFO['video_size'] = self.resolution_map[self.res_dropdown.value][::-1]
        
        self.FILE_INFO['bytes'] = self.find_stream_by_res(self.res_dropdown.value).filesize
        self.bytes.value = f'Size: {self.FILE_INFO["bytes"]/1e6:.2f} MB'
        self.update()

    def show_download_button(self, e):
        self.download_button.visible = True
        self.load_ok.visible = False
        self.url_field.hint_text = 'URL del video de YouTube..'
        self.update()
    
    def progress_youtube_download(self, stream, chunk, bytes_remaining):
        self.p_download.controls[0].value = 1-bytes_remaining/self.FILE_INFO['bytes']
        self.update()

    def show_info_sect(self, e):
        if self.res_dropdown.options != []:
            self.res_dropdown.options = []
            self.clear_FILE_params()
            self.res_dropdown.visible = False
            self.c_info.visible = False
            self.c_clips.visible = False
            self.update()

        if self.text_result_download.value != '':
            self.clear_for_resplit()
        
        self.download_button.visible = False
        self.load_progress.visible = True
        self.update()

        try:
            yt = YouTube(self.url_field.value, on_progress_callback=self.progress_youtube_download)
        except:
            self.url_field.value = ''
            self.url_field.hint_text = 'URL inválida'
            self.load_progress.visible = False
            self.download_button.visible = True
            self.update()
            return
        
        self.FILE_NAME = 'output.mp4'
        self.FILE_PATH = os.getcwd()

        self.FILE_INFO['duration'] = yt.length
        self.FILE_INFO['image_url'] = yt.thumbnail_url 

        self.streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()

        for res in self.streams:
            self.res_dropdown.options.append(ft.dropdown.Option(res.resolution))
        self.res_dropdown.value = res.resolution
        self.res_callback(None)
        self.res_dropdown.visible = True
        
        self.load_progress.visible = False
        self.load_ok.visible = True

        minutes, seconds = divmod(self.FILE_INFO['duration'], 60)
        self.duration.value = f"Duration: {self.FILE_INFO['duration']} s ({int(minutes)}:{int(seconds)})"
        self.bytes.value = f"Size: {self.FILE_INFO['bytes'] / 1e6:.2f} MB"
        self.img.src = self.FILE_INFO['image_url']
        self.video_title.value = yt.title
        self.c_info.visible = True
        self.show_output_dir()
        self.show_split_params_sect()
        self.update()
    
    def show_split_params_sect(self):
        t = self.FILE_INFO['duration']
        self.ti.value = '0.0'
        self.tf.value = t
        self.dt.value = min(30.0, t)
        self.c_clips.visible = True
        self.update_clips_number()

    def cotas_ti_callback(self, e):
        if re.match(r'^[\d.,]+$', str(self.ti.value)):
            if float(self.ti.value) >= float(self.tf.value):
                self.ti.value = float(self.tf.value) - 1
            elif float(self.ti.value) < 0:
                self.ti.value = 0.0
        else:
            self.ti.value = 0.0
        self.cotas_dt_callback(self)

    def cotas_tf_callback(self, e):
        t = self.FILE_INFO['duration']
        if re.match(r'^[\d.,]+$', str(self.tf.value)):
            if float(self.tf.value) <= float(self.ti.value):
                self.tf.value = float(self.ti.value) + 1
            elif float(self.tf.value) > t:
                self.tf.value = t
        else:
            self.tf.value = t
        self.cotas_dt_callback(self)

    def cotas_dt_callback(self, e):
        if re.match(r'^[\d.,]+$', str(self.dt.value)):
            if float(self.dt.value) < 1:
                self.dt.value = 1.0
            if float(self.dt.value) > float(self.tf.value)-float(self.ti.value):
                self.dt.value = float(self.tf.value)-float(self.ti.value)
        else:
            self.dt.value = 30.0
        self.update_clips_number()

    def update_clips_number(self):
        if (float(self.tf.value) - float(self.ti.value))%float(self.dt.value) == 0:
            self.n_clips.value = int((float(self.tf.value) - float(self.ti.value))//float(self.dt.value))
        else:
            self.n_clips.value = int((float(self.tf.value) - float(self.ti.value))//float(self.dt.value)) + 1
        self.update()

    def find_stream_by_res(self, res):
        for stream in self.streams:
            if stream.resolution == res:
                return stream
    
    def split_callback(self, e):
        out_path = os.path.join(self.out_field.value, 'output_folder')
        file_path = os.path.join(out_path, self.FILE_NAME)

        res = self.FILE_INFO['video_size']

        if not os.path.exists(out_path):
            os.mkdir(out_path)
        else:
            delete_directory_contents(out_path)
        
        if self.text_result_save.value != '':
            self.clear_for_resplit()

        t_end = float(self.tf.value)
        t_start = float(self.ti.value)
        clip_duration = float(self.dt.value)

        self.page.splash = ft.ProgressBar()
        self.page.update()

        self.text_result_download.value = 'Descargando video de Youtube...'
        self.p_download.visible = True
        self.whole.disabled = True
        self.update()

        stream = self.find_stream_by_res(self.res_dropdown.value)
        if os.path.exists(file_path):
            pc_file_res = list(ffmpeg_parse_infos(file_path)['video_size'])
            yt_file_res = list(res)
            yt_file_res.sort()
            if pc_file_res != yt_file_res:
                stream.download(output_path=out_path, filename=self.FILE_NAME)
        else:
            stream.download(output_path=out_path, filename=self.FILE_NAME)

        self.p_download.visible = False
        self.ch_download.visible = True
        self.update()

        self.text_result_load.value = 'Cargando el video...'
        self.p_load.visible = True
        self.update()

        with mp.VideoFileClip(file_path, target_resolution = res).subclip(t_start, t_end) as clip:
            self.p_load.visible = False
            self.ch_load.visible = True
            self.update()

            n = int((t_end - t_start)//clip_duration)
            rest_time = (t_end - t_start)%clip_duration

            self.text_result_proc.value = 'Procesando el video...'
            self.p_proc.visible = True
            self.update()

            clips = [clip.subclip(clip_duration*i, clip_duration*(i+1)) for i in np.arange(n)]; 
            if rest_time != 0: clips.append(clip.subclip(n*clip_duration, t_end-t_start))
            
            self.p_proc.visible = False
            self.ch_proc.visible = True
            self.update()

            self.text_result_save.value = 'Guardando los clips...'
            self.p_save.visible = True
            self.update()

            for i in np.arange(n):
                clips[i].write_videofile('{}/{}{}'.format(out_path, i+1, '.mp4'))
            if rest_time != 0: clips[n].write_videofile('{}/{}{}'.format(out_path, n+1, '.mp4'))

            self.p_save.visible = False
            self.ch_save.visible = True
        
        self.whole.disabled = False
        self.update()

        self.page.splash = None
        self.page.update()

class page_properties():
    def __init__(self, page):
        self.page = page
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.title = 'Video Splitter' + ' - ' + 'v' + VERSION
        self.page.horizontal_alignment = 'center'
        #self.page.vertical_alignment = 'center'
        self.page.window_always_on_top = True
        self.page.window_width = 450
        self.page.window_height = 800
        self.page.window_resizable = False
        self.page.padding = 10
        self.page.scroll = True

class Options(UserControl):
    def __init__(self, page, expand=1):
        super().__init__()
        self.page = page
        self.expand = expand

    def build(self):
        self.sw1 = ft.Switch(on_change=self.swith_theme, label="Dark mode", value=True)
        self.sw2 = ft.Switch(on_change=self.swith_on_top, label="On Top", value=True)
        
        pb = ft.PopupMenuButton(
            items=[
                ft.PopupMenuItem(content=Row([self.sw1, Icon(icons.DARK_MODE, size=20)])),
                ft.PopupMenuItem(content=Row([self.sw2, Icon(icons.ARROW_UPWARD, size=20)])),
            ]
        )
        return Row([pb], expand=self.expand)

    def swith_on_top(self, e):
        self.page.window_always_on_top = not self.page.window_always_on_top
        self.update_all()

    def swith_theme(self, e):
        self.page.theme_mode = ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        cont.bgcolor = '#212121' if self.page.theme_mode == ft.ThemeMode.DARK else '#f0f0f0'
        div.color = 'white' if self.page.theme_mode == ft.ThemeMode.DARK else 'black'
        self.update_all()

    def update_all(self):
        self.page.update()
        self.update()


def main(page: Page):
    global cont, div
    page_properties(page)

    cont = Container(height=800, padding=5, bgcolor='#212121', border_radius=5)

    # Encabezado
    enc = Row([
        Options(page, expand = 1),
        Row([
            Text(
                f'Versión {VERSION[:-1]}2 en desarrollo', 
                size=15, 
                color='red',
                text_align=ft.TextAlign.END,
            ),
        ], expand=1),
    ])

    # Divisor
    div = ft.Divider(height=1, color='white')


    t = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="PC",
                icon=icons.DRIVE_FOLDER_UPLOAD_ROUNDED,
                content= Video_from_PC(page)
            ),
            ft.Tab(
                text="Youtube",
                icon=icons.LINK_ROUNDED,
                content= Video_from_YT(page)
            ),
        ],
        expand=1,
    )

    cont.content=Column([enc, div, t], expand=1)
    page.add(cont)

ft.app(target=main)

# para armar la app.exe ejecutar en la terminal:
# flet pack app.py
