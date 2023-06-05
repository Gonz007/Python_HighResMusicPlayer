import sys
import os
import time
import pygame
from random import randint, shuffle
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QFileDialog,
    QMenuBar,
    QMenu,
    QAction,
    QSlider,
)
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt, QTimer, QTime

class BasicMusicPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.added_folders = set()
        self.shuffle_mode = False
        self.shuffle_list = []
        self.last_played_music_file = None
        self.last_played_position = 0
        self.setWindowTitle('Auto Bee music')
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()
        self.mixer = pygame.mixer
        self.mixer.init()
        self.music_file = None
        self.paused = False
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(1000)
        self.slider_dragging = False
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)

        # Establecer una hoja de estilo en cascada para la aplicación
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
            }
            QPushButton, QSlider {
                background-color: #3d3d3d;
                color: white;
            }
            QListWidget, QLabel {
                background-color: #4d4d4d;
                color: white;
            }
        """)

# Inicializa la interfaz de usuario y sus componentes
    def init_ui(self):
        self.layout = QVBoxLayout()

        # Crear la barra de menú
        self.menu_bar = QMenuBar()
        self.file_menu = QMenu("Archivo", self)
        self.add_folder_action = QAction("Agregar carpeta", self)
        self.file_menu.addAction(self.add_folder_action)
        self.menu_bar.addMenu(self.file_menu)

        self.layout.setMenuBar(self.menu_bar)

        # Crear una disposición horizontal para botones y carátula del álbum
        self.button_and_cover_layout = QHBoxLayout()

        # Crear y agregar botones
        self.prev_button = QPushButton('Anterior')
        self.play_button = QPushButton('Reproducir')
        self.next_button = QPushButton('Siguiente')
        self.shuffle_button = QPushButton('Shuffle OFF')

        self.prev_button.clicked.connect(self.prev_audio)
        self.play_button.clicked.connect(self.play_pause_audio)
        self.next_button.clicked.connect(self.next_audio)
        self.shuffle_button.clicked.connect(self.toggle_shuffle_mode)
        self.add_folder_action.triggered.connect(self.open_folder)

        self.button_and_cover_layout.addWidget(self.prev_button)
        self.button_and_cover_layout.addWidget(self.play_button)
        self.button_and_cover_layout.addWidget(self.next_button)
        self.button_and_cover_layout.addWidget(self.shuffle_button)
        self.current_time_label = QLabel("00:00")
        self.layout.addWidget(self.current_time_label)
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderReleased.connect(self.change_position)
        self.layout.addWidget(self.progress_slider)
        # Crear y agregar la etiqueta para la carátula del álbum
        self.cover_label = QLabel()
        self.show_default_cover()  # Agregar esta línea para mostrar el cuadro negro predeterminado
        self.button_and_cover_layout.addWidget(self.cover_label)
        # Crear y agregar la etiqueta para la carátula del álbum


        

        # Agregar la disposición horizontal al diseño principal
        self.layout.addLayout(self.button_and_cover_layout)

        self.music_list = QListWidget()
        self.layout.addWidget(self.music_list)

        self.setLayout(self.layout)

        self.music_list.itemDoubleClicked.connect(self.play_selected)

        self.load_default_music_folder()

        self.volume_slider = QSlider(Qt.Vertical)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickInterval(50)
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.button_and_cover_layout.addWidget(self.volume_slider)

# Agregar un control deslizante para la barra de progreso

# Ajusta el volumen del reproductor de música
    def set_volume(self, value):
        volume = value / 100.0
        self.mixer.music.set_volume(volume)

# Guarda las carpetas de música en un archivo de configuración
    def save_config_file(self):
        with open("config.txt", "w") as f:
            for folder in self.added_folders:
                f.write(folder + "\n")

# Abre una carpeta y carga su contenido en la lista de música
    def open_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de música")
        if folder_name:
            if folder_name not in self.added_folders: # verificar si la carpeta ya ha sido agregada
                self.added_folders.add(folder_name)
                self.update_folders_menu()
                self.load_music_from_folder(folder_name)
                self.save_config_file() # llama a la función para guardar la carpeta en el archivo de configuración

# Carga la carpeta de música predeterminada y la lista de música
    def load_default_music_folder(self):
        default_music_folder = os.path.join(os.path.expanduser("~"), "Music")
        if os.path.exists(default_music_folder):
            for file in os.listdir(default_music_folder):
                if file.lower().endswith(('.flac', '.mp3','.wav')):
                    self.music_list.addItem(os.path.join(default_music_folder, file))
        config_file = "config.txt"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                for line in f:
                    folder = line.strip()
                    if os.path.isdir(folder) and folder not in self.added_folders:
                        self.added_folders.add(folder)
                        self.load_music_from_folder(folder)
            self.update_folders_menu()

# Activa o desactiva el modo aleatorio
    def toggle_shuffle_mode(self):
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            self.shuffle_button.setText("Shuffle ON")
            self.create_shuffle_list()
        else:
            self.shuffle_button.setText("Shuffle OFF")
            self.shuffle_list = []

# Crea una lista aleatoria de índices para el modo aleatorio
    def create_shuffle_list(self):


    
        self.shuffle_list = list(range(self.music_list.count()))
        shuffle(self.shuffle_list)

# Reproduce o pausa la música actualmente seleccionada
    def play_pause_audio(self):
        if not self.music_file:
            random_index = randint(0, self.music_list.count() - 1)
            self.music_list.setCurrentRow(random_index)
            self.music_file = self.music_list.currentItem().text()

        if self.paused:
            self.mixer.music.unpause()
            self.paused = False
            self.play_button.setText('Pausar')
        elif self.music_file:
            if self.mixer.music.get_busy():
                self.mixer.music.pause()
                self.paused = True
                self.play_button.setText('Reproducir')
            else:
                self.mixer.music.load(self.music_file)
                self.mixer.music.play()
                self.show_cover_art(self.music_file)
                self.play_button.setText('Pausar')

# Reproduce el audio anterior en la lista
# Retrocede al audio anterior en la lista
    def prev_audio(self):
        current_index = self.music_list.currentRow()
        if self.mixer.music.get_pos() < 5000:  # Si se ha reproducido menos de 3 segundos
            if self.shuffle_mode:
                prev_index = self.shuffle_list.index(current_index) - 1
                if prev_index < 0:
                    prev_index = len(self.shuffle_list) - 1
                current_index = self.shuffle_list[prev_index]
            else:
                current_index -= 1
                if current_index < 0:
                    current_index = self.music_list.count() - 1
        else:
            # Agrega esta línea para reiniciar la posición del slider
            self.progress_slider.setValue(0)

        self.music_list.setCurrentRow(current_index)
        self.music_file = self.music_list.currentItem().text()
        self.play_audio()


# Reproduce el siguiente audio en la lista
    def next_audio(self):
        current_index = self.music_list.currentRow()
        if self.shuffle_mode:
            next_index = self.shuffle_list.index(current_index) + 1
            if next_index >= len(self.shuffle_list):
                next_index = 0
            current_index = self.shuffle_list[next_index]
        else:
            current_index += 1
            if current_index >= self.music_list.count():
                current_index = 0

        self.music_list.setCurrentRow(current_index)
        self.music_file = self.music_list.currentItem().text()
        self.play_audio()

# Detiene la reproducción del audio
    def stop_audio(self):
        if self.mixer.music.get_busy():
            self.mixer.music.stop()
            self.paused = False

# Actualiza el menú de carpetas en la barra de menú
    def update_folders_menu(self):
        self.file_menu.clear()
        self.file_menu.addAction(self.add_folder_action)

        for folder in self.added_folders:
            folder_action = QAction(folder, self, checkable=True)
            folder_action.setChecked(True)
            folder_action.triggered.connect(lambda state, f=folder: self.toggle_folder(f, state))
            self.file_menu.addAction(folder_action)

# Muestra u oculta la música de una carpeta específica
    def toggle_folder(self, folder, state):
        if state:
            self.load_music_from_folder(folder)
        else:
            self.remove_music_from_folder(folder)

# Carga la música de una carpeta en la lista de música
    def load_music_from_folder(self, folder_name):
        added_songs = set()
        for file in os.listdir(folder_name):
            if file.lower().endswith(('.flac', '.mp3', '.wav')):
                song_path = os.path.join(folder_name, file)
                if song_path not in added_songs:
                    self.music_list.addItem(song_path)
                    added_songs.add(song_path)

        # Eliminar la música de la carpeta por defecto si se agregó otra carpeta
        default_music_folder = os.path.join(os.path.expanduser("~"), "Music")
        if folder_name != default_music_folder:
            self.remove_music_from_folder(default_music_folder)

# Elimina la música de una carpeta de la lista de música
    def remove_music_from_folder(self, folder_name):
        for i in range(self.music_list.count() - 1, -1, -1):
            item = self.music_list.item(i)
            if os.path.dirname(item.text()) == folder_name:
                self.music_list.takeItem(i)

# Reproduce el audio seleccionado en la lista
    def play_selected(self):
        self.music_file = self.music_list.currentItem().text()
        self.play_audio()

# Reproduce el archivo de música especificado
    def play_audio(self):
        if self.music_file:
            # Agrega estas líneas para cargar la información de la última canción reproducida
            if self.music_file == self.last_played_music_file:
                start_pos = self.last_played_position
            else:
                start_pos = 0

            # Agrega estas líneas para guardar la información de la última canción reproducida
            self.last_played_position = self.mixer.music.get_pos() // 1000
            self.last_played_music_file = self.music_file
            # Guardar el tiempo de inicio de la canción actual
            self.start_time = time.time()

            self.mixer.music.load(self.music_file)
            # Agrega esta línea para reproducir la canción desde el segundo de reproducción guardado
            self.mixer.music.play(start=start_pos)
            self.show_cover_art(self.music_file)
            self.play_button.setText('Pausar')
            self.paused = False

    def show_default_cover(self):
        # Crear un cuadro negro de tamaño fijo (300x300)
        pixmap = QPixmap(300, 300)
        pixmap.fill(Qt.black)
        self.cover_label.setPixmap(pixmap)
# Muestra la carátula del álbum para el archivo de música especificado
    def show_cover_art(self, music_file):
        artwork_data = None

        if music_file.lower().endswith('.mp3'):
            audio = MP3(music_file)
            if 'APIC:' in audio:
                artwork_data = audio['APIC:'].data

        elif music_file.lower().endswith('.flac'):
            audio = FLAC(music_file)
            if audio.pictures:
                artwork_data = audio.pictures[0].data

        # Crear un cuadro negro de tamaño fijo (500x600)
        pixmap = QPixmap(300, 300)
        pixmap.fill(Qt.black)

        if artwork_data:
            image = QImage.fromData(artwork_data)
            cover_pixmap = QPixmap.fromImage(image)

            # Ajustar la carátula al cuadrado manteniendo su relación de aspecto
            cover_pixmap = cover_pixmap.scaled(300, 300, aspectRatioMode=Qt.KeepAspectRatio)

            # Superponer la carátula del álbum en el cuadro negro
            painter = QPainter(pixmap)
            cover_x = (pixmap.width() - cover_pixmap.width()) // 2
            cover_y = (pixmap.height() - cover_pixmap.height()) // 2
            painter.drawPixmap(cover_x, cover_y, cover_pixmap)
            painter.end()

        self.cover_label.setPixmap(pixmap)
    

#En progreso
    current_time_str = "00:00"
    total_length_str = "00:00"


    def slider_pressed(self):
        self.slider_dragging = True

    def slider_released(self):
        if self.music_file and self.slider_dragging:
            self.slider_dragging = False
            self.change_position()



    def update_progress(self):
        global current_time_str, total_length_str
        if self.mixer.music.get_busy():
            current_pos = self.mixer.music.get_pos() // 1000
            if self.music_file.lower().endswith('.mp3'):
                audio = MP3(self.music_file)
                total_length = int(audio.info.length)
            elif self.music_file.lower().endswith('.flac'):
                audio = FLAC(self.music_file)
                total_length = int(audio.info.length)
            elif self.music_file.lower().endswith('.wav'):
                total_length = int(pygame.mixer.Sound(self.music_file).get_length())

            self.progress_slider.setMinimum(0)
            self.progress_slider.setMaximum(total_length)
            
            if not self.slider_dragging:
                self.progress_slider.setSliderPosition(current_pos)

            current_time_str = QTime(0, 0).addSecs(current_pos).toString("mm:ss")
            total_length_str = QTime(0, 0).addSecs(total_length).toString("mm:ss")
            time_str = f"{current_time_str}/{total_length_str}"
            self.current_time_label.setText(time_str)
        else:
            self.progress_slider.setMinimum(0)
            self.progress_slider.setMaximum(0)
            self.progress_slider.setValue(0)
            self.current_time_label.setText("00:00")



    def change_position(self):
        if self.music_file:
            pos = self.progress_slider.value()
            if self.music_file.lower().endswith('.mp3'):
                audio = MP3(self.music_file)
            elif self.music_file.lower().endswith('.flac'):
                audio = FLAC(self.music_file)
            elif self.music_file.lower().endswith('.wav'):
                audio = int(pygame.mixer.Sound(self.music_file).get_length())

            self.mixer.music.stop()
            pos_sec = pos
            self.mixer.music.play(start=pos_sec)
            time_str = f"{current_time_str}/{total_length_str}"
            self.current_time_label.setText(time_str)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = BasicMusicPlayer()
    player.show()
    sys.exit(app.exec_())