# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import datetime
import glob
import os
import time
from os.path import dirname, abspath
import subprocess

from mycroft.skills.core import MycroftSkill, intent_file_handler
# from mycroft.util import play_wav
# from mycroft.device import device as d_hw
from mycroft.util.parse import extract_number
from mycroft.util.log import LOG
from mycroft.util import play_wav
from subprocess import DEVNULL, STDOUT
from ovos_utils.gui import is_gui_installed


class UsbCamSkill(MycroftSkill):

    def __init__(self):
        super(UsbCamSkill, self).__init__(name="UsbCamSkill")
        self.pic_path = os.path.join(self.configuration_available["dirVars"]["picsDir"], "UsbCam")
        self.vid_path = os.path.join(self.configuration_available["dirVars"]["videoDir"], "UsbCam")

        sound_path = dirname(abspath(__file__)) + '/res/wav/'

        self.notify_sound = sound_path + 'notify.wav'
        self.shutter_sound = sound_path + 'shutter.wav'
        self.record_sound = sound_path + 'beep.wav'

        self.image_extension = ".jpg"
        self.video_extension = ".avi"
        if not self.server:
            # self.ensure_dir(self.pic_path)
            # self.ensure_dir(self.vid_path)
            try:
                camera_id = int(self.configuration_available["devVars"].get("camDev", 0))
                cam_devs = glob.glob("/dev/video*")
                if len(cam_devs) > 0:
                    if f"/dev/video{camera_id}" in cam_devs:
                        self.cam_dev = f"/dev/video{camera_id}"
                    else:
                        self.cam_dev = sorted(cam_devs)[0]
                else:
                    self.cam_dev = None
            except Exception as e:
                self.cam_dev = None
                LOG.error(e)

        self.vidid = 0

    def initialize(self):
        # Uses `duration` from mycroft-timer skill
        self.register_entity_file('duration.entity')

    @intent_file_handler('TakePicIntent.intent')
    def handle_take_pic_intent(self, message):
        if ("picture" or "pic" or "photo") in message.data.get("utterance"):
            LOG.info("In picture")
            LOG.debug(message.data)
            today = datetime.datetime.today()
            user = self.get_utterance_user(message)
            pic_path = os.path.join(self.pic_path, user)
            if not os.path.exists(pic_path):
                LOG.debug(f"Creating pictures path: {pic_path}")
                os.makedirs(pic_path)
            newest_pic = os.path.join(pic_path, "user_pic" + str(today).replace(" ", "_") + self.image_extension) if \
                ("user" or "my") in message.data.get("utterance") else os.path.join(pic_path,
                                                                                    str(today).replace(" ", "_")
                                                                                    + self.image_extension)
            try:
                LOG.info(type(self.request_from_mobile(message)))
                if self.request_from_mobile(message):
                    self.speak_dialog("LaunchCamera", private=True)
                    # self.speak("MOBILE-INTENT PICTURE")
                    self.mobile_skill_intent("picture", {}, message)
                    # self.socket_io_emit('picture', '', message.context["flac_filename"])
                elif self.server:
                    self.speak_dialog("ServerNotSupported", private=True)
                else:
                    if self.cam_dev is not None:
                        play_wav(self.shutter_sound)
                        LOG.debug(f"TIME: to_speak, {time.time()}, {message.data['utterance']}, {message.context}")
                        os.system(f"fswebcam -d {self.cam_dev} --delay 2 --skip 2 "
                                  f"-r 1280x720 --no-banner {newest_pic}")
                        time.sleep(1)
                        self.display_image(image=newest_pic)
                    else:
                        self.speak_dialog("NoCamera", private=True)
            except Exception as e:
                LOG.error(e)
            finally:
                if ("user" or "my") in message.data.get("utterance"):
                    self.save_user_info(newest_pic, "picture")

    @intent_file_handler('ShowLastIntent.intent')
    def handle_show_last_intent(self, message):
        if "picture" in message.data.get("utterance"):
            if self.request_from_mobile(message):
                # self.speak("MOBILE-INTENT LATEST_PICTURE")
                self.mobile_skill_intent("show_pic", {}, message)
                # self.socket_io_emit('show_pic', '', message.context["flac_filename"])
            elif self.server:
                self.speak_dialog("ServerNotSupported", private=True)
            else:
                self.display_latest_pic(profile_pic=("user" or "my") in message.data.get("utterance"),
                                        requested_user=self.get_utterance_user(message))
        else:
            if self.request_from_mobile(message):
                # self.speak("MOBILE-INTENT LATEST_VIDEO")
                self.mobile_skill_intent("show_vid", {}, message)
                # self.socket_io_emit('show_vid', '', message.context["flac_filename"])
            elif self.server:
                self.speak_dialog("ServerNotSupported", private=True)
            else:
                self.display_latest_vid(profile_vid=("user" or "my") in message.data.get("utterance"),
                                        requested_user=self.get_utterance_user(message))

    def save_user_info(self, param, field):
        # self.create_signal("NGI_YAML_user_update")
        self.user_config.update_yaml_file(header="user", sub_header=field, value=param)

    def display_latest_pic(self, secs=15, notify=True, profile_pic=False, requested_user="local"):
        try:
            latest_pic = self.newest_file_in_dir(os.path.join(self.pic_path, requested_user),
                                                 self.image_extension) if not profile_pic \
                else self.user_info_available["user"]["picture"]
            if latest_pic and os.path.isfile(latest_pic):
                self.speak_dialog("ShowLatest", private=True)
                self.display_image(latest_pic, secs=secs, notify=notify)
            else:
                self.speak_dialog("NothingToShow", {"kind": "pictures"}, private=True)
        except Exception as e:
            LOG.error(e)
            self.speak_dialog("NothingToShow", {"kind": "pictures"}, private=True)

    def display_latest_vid(self, profile_vid=False, requested_user="local"):
        try:
            latest_vid = self.newest_file_in_dir(os.path.join(self.vid_path, requested_user),
                                                 self.video_extension) if not profile_vid \
                else self.user_info_available["user"]["video"]
            if self.gui_enabled:
                # TODO: Display video in gui DM
                pass
            if os.path.isfile(latest_vid):
                self.speak_dialog("ShowLatest", private=True)
                subprocess.Popen(["mpv", str(latest_vid)])
            else:
                self.speak_dialog("NothingToShow", {"kind": "videos"}, private=True)
        except Exception as e:
            LOG.error(e)
            self.speak_dialog("NothingToShow", {"kind": "videos"}, private=True)

    def display_image(self, image, secs=15, notify=True):
        # notification sound
        if notify:
            play_wav(self.notify_sound)

        # method of displaying image
        if self.configuration_available["devVars"]["devType"] in ("pi", "neonPi"):
            os.system("sudo /home/pi/ngi_code/scripts/splash/splash_start " + image + " " + str(secs))
        elif is_gui_installed():
            self.gui.show_image(image, fill="PreserveAspectFit")
            self.clear_gui_timeout(secs)
        else:
            os.system("timeout " + str(secs) + " eog " + image)

    @intent_file_handler('TakeVidIntent.intent')
    def handle_take_vid_intent(self, message):
        if "video" in message.data.get("utterance"):
            try:
                duration = message.data["duration"]
                heard_duration = True
            except KeyError:
                duration = "5 seconds"
                heard_duration = False
                # if not self.server and not message.data.get("mobile"):
                #     self.speak_dialog("DefaultDuration", {"duration": duration}, private=True)

            if self.request_from_mobile(message):
                self.speak_dialog("LaunchCamera", private=True)
                # self.speak("MOBILE-INTENT VIDEO")
                self.mobile_skill_intent("video", {}, message)
                # self.socket_io_emit('video', '', message.context["flac_filename"])
            elif self.server:
                self.speak_dialog("ServerNotSupported", private=True)
            else:
                # Determine Duration
                secs = self._extract_duration(duration)

                # Sub pic for 1s vid
                if secs == 1 or secs is None:
                    self.speak_dialog("PictureInsteadOfVideo", private=True)
                    time.sleep(4)
                    self.handle_take_pic_intent(message)
                    return

                playback = ('no playback' or 'without playback') in message.data.get("utterance")

                # Determine if we can handle this
                if self.request_from_mobile(message):
                    self.mobile_skill_intent("video", {"duration": duration}, message)
                    # self.socket_io_emit('video', f'&duration={duration}', message.context["flac_filename"])
                    self.speak("LaunchCamera", private=True)
                elif self.server:
                    self.speak_dialog("ServerNotSupported", private=True)
                elif self.cam_dev:
                    if heard_duration:
                        self.speak_dialog("StartRecording", {"duration": duration}, private=True)
                    else:
                        self.speak_dialog("DefaultDuration", {"duration": duration}, private=True)
                    self.vidid += 1
                    play_wav(self.record_sound)
                    vid_path = os.path.join(self.vid_path, self.get_utterance_user(message))
                    if not os.path.exists(vid_path):
                        LOG.debug(f"Creating video path: {vid_path}")
                        os.makedirs(vid_path)

                    path = vid_path + "v" + str(self.vidid) + ".avi" if not\
                        ("user" or "my") in message.data.get("utterance") else \
                        vid_path + "user_video_v" + str(self.vidid) + ".avi"
                    os.system(f"streamer -f rgb24 -i {self.cam_dev} -t 00:00:{secs} -o {path}.avi")
                    play_wav(self.notify_sound)
                    if ("user" or "my") in message.data.get("utterance"):
                        self.save_user_info(path, 'video')

                    if playback:
                        time.sleep(1)
                        subprocess.Popen(["mpv", path], stdout=DEVNULL, stderr=STDOUT)
                else:
                    self.speak_dialog("NoCamera", private=True)

    def _extract_duration(self, text):
        if not text:
            return None

        # return the duration in seconds
        num = extract_number(text.replace("-", " "))
        unit = 1  # default to secs

        if any(i.strip() in text for i in self.translate_list('second')):
            unit = 1
        elif any(i.strip() in text for i in self.translate_list('minute')):
            unit = 60
        elif any(i.strip() in text for i in self.translate_list('hour')):
            unit = 60 * 60

        if not num and unit == 1:
            return None
        elif not num:
            return unit
        else:
            return unit * num

    # @staticmethod
    # def stop():
    #     pass

    @staticmethod
    def ensure_dir(file_path):
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

    # def newest_file_in_dir(self, path):
    #     files = os.listdir(path)
    #     paths = [os.path.join(path, basename) for basename in
    #              ([f for f in files if str(f).endswith(self.image_extension) or str(f).endswith(self.video_extension)]
    #               if files else [])]
    #     return max(paths, key=os.path.getmtime)

    def stop(self):
        pass


def create_skill():
    return UsbCamSkill()
