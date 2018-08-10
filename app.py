import time
from typing import TYPE_CHECKING

from api.discord_presence import DiscordPresence
from api.kodi import Kodi
from util.config import Configurations
from util.system_tray import SysTray

running = True
if TYPE_CHECKING:
    pass


class App:
    play_icon = '\u25B6'
    pause_icon = '\u275A\u275A'
    running = True
    update_rate = 1

    def __init__(self, configuration):
        self._config = configuration

    def stop(self):
        """
        Stop the application from running.
        """
        self.running = False

    def get_kodi_connection(self):
        """
        Returns a new Kodi connection with recent configurations.

        :return: new Kodi instance
        :rtype: Kodi
        """
        return Kodi(self._config.kodi_ip, self._config.kodi_port, self._config.kodi_username,
                    self._config.kodi_password)

    def update_discord(self, discord: DiscordPresence, play_info: dict):
        """
        Updates the Discord Rich Presence display.

        :param discord: Discord connection.
        :type discord: DiscordPresence
        :param play_info: Information about the movie/show.
        :type play_info: dict
        """
        if play_info.get('title') is not None:
            discord.connect()
            icon = '{icon}'.format(icon=self.play_icon if play_info['playing'] else self.pause_icon)
            time_format = '{time[0]}:{time[1]:02d}:{time[2]:02d}'
            formatted_time = time_format.format(time=play_info['current_time'])
            formatted_total_time = time_format.format(time=play_info['total_time'])
            discord.update_status(details='{title}'.format(**play_info), large_image=play_info['type'],
                                  state='{icon} {time}/{total_time}'.format(icon=icon, time=formatted_time,
                                                                            total_time=formatted_total_time))
        else:
            discord.disconnect()

    def run(self):
        """
        Main running thread.
        """
        discord = DiscordPresence(self._config.client_id)
        kodi = self.get_kodi_connection()
        while self.running:
            time.sleep(self.update_rate)
            if self.update_rate > 1:
                kodi = self.get_kodi_connection()  # refresh settings, since it was put on timeout
            kodi_info = kodi.get_currently_playing_item()
            if not kodi_info['failed_connection']:
                self.update_rate = 1
                self.update_discord(discord, kodi_info)
            else:
                self.update_rate = 30


if __name__ == '__main__':
    config = Configurations()
    app = App(config)
    sys_tray = SysTray(app, config)
    sys_tray.start()
    app.run()
