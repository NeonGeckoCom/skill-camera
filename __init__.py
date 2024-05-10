# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import datetime
import glob
import os
import time
from os.path import dirname, abspath
import subprocess

from neon_utils.file_utils import get_most_recent_file_in_dir
from neon_utils.message_utils import request_from_mobile

from ovos_workshop.decorators import intent_handler
from lingua_franca.parse import extract_number
from ovos_utils.sound import play_audio
from subprocess import DEVNULL, STDOUT
from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements
from ovos_utils.gui import is_gui_installed
from neon_utils.skills.neon_skill import NeonSkill
from neon_utils.message_utils import get_message_user


class CameraSkill(NeonSkill):
    def __init__(self, **kwargs):
        NeonSkill.__init__(self, **kwargs)
        self.pic_path = os.path.expanduser("~/Pictures/Neon")
        self.vid_path = os.path.expanduser("~/Videos/Neon")
        os.makedirs(self.pic_path, exist_ok=True)
        os.makedirs(self.vid_path, exist_ok=True)
        sound_path = dirname(abspath(__file__)) + '/res/wav/'  # TODO: This should probably use resolve_resource_file DM

        self.notify_sound = sound_path + 'notify.wav'
        self.shutter_sound = sound_path + 'shutter.wav'
        self.record_sound = sound_path + 'beep.wav'

        self.image_extension = ".jpg"
        self.video_extension = ".avi"
        try:
            camera_id = 0  # int(self.local_config.get("devVars", {}).get("camDev", 0))
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

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(network_before_load=False,
                                   internet_before_load=False,
                                   gui_before_load=False,
                                   requires_internet=False,
                                   requires_network=False,
                                   requires_gui=False,
                                   no_internet_fallback=True,
                                   no_network_fallback=True,
                                   no_gui_fallback=True)

    # TODO: Move to __init__ after stable ovos-workshop
    def initialize(self):
        # Uses `duration` from mycroft-timer skill
        self.register_entity_file('duration.entity')
        # Register Camera GUI Events
        self.gui.register_handler(
            "CameraSkill.ViewPortStatus", self.handle_camera_status
        )
        self.gui.register_handler(
            "CameraSkill.EndProcess", self.handle_camera_completed
        )

    def handle_camera_completed(self, _=None):
        """Close the Camera GUI when finished."""
        self.gui.remove_page("Camera.qml")
        self.gui.release()

    def handle_camera_status(self, message):
        """Handle Camera GUI status changes."""
        current_status = message.data.get("status")
        if current_status == "generic":
            self.gui["singleshot_mode"] = False
        if current_status == "imagetaken":
            self.gui["singleshot_mode"] = False
        if current_status == "singleshot":
            self.gui["singleshot_mode"] = True

    def handle_camera_activity(self, activity):
        """Perform camera action.

        Arguments:
            activity (str): the type of action to take, one of:
                "generic" - open the camera app
                "singleshot" - take a single photo
        """
        self.gui["save_path"] = self.pic_path
        if activity == "singleshot":
            self.gui["singleshot_mode"] = True
        if activity == "generic":
            self.gui["singleshot_mode"] = False
        self.gui.show_page("Camera.qml", override_idle=60)

    @intent_handler('TakePicIntent.intent')
    def handle_take_pic_intent(self, message):
        if ("picture" or "pic" or "photo") in message.data.get("utterance"):
            LOG.info("In picture")
            LOG.debug(message.data)
            today = datetime.datetime.today()
            user = get_message_user(message) or os.environ.get('USER', os.environ.get('USERNAME'))
            pic_path = os.path.join(self.pic_path, user)
            if not os.path.exists(pic_path):
                LOG.debug(f"Creating pictures path: {pic_path}")
                os.makedirs(pic_path)
            newest_pic = os.path.join(pic_path, "user_pic" + str(today).replace(" ", "_") + self.image_extension) if \
                ("user" or "my") in message.data.get("utterance") else os.path.join(pic_path,
                                                                                    str(today).replace(" ", "_")
                                                                                    + self.image_extension)
            try:
                # LOG.info(type(self.request_from_mobile(message)))
                if request_from_mobile(message):
                    self.speak_dialog("LaunchCamera", private=True)
                    # TODO
                    # self.speak("MOBILE-INTENT PICTURE")
                    # self.mobile_skill_intent("picture", {}, message)
                    # self.socket_io_emit('picture', '', message.context["flac_filename"])
                elif message.context.get("klat_data"):
                    self.speak_dialog("ServerNotSupported", private=True)
                elif self.gui_enabled:
                    self.gui["singleshot_mode"] = False
                    self.handle_camera_activity("singleshot")
                    self.bus.emit(message.forward("neon.metric", {"name": "audio-response"}))
                else:
                    if self.cam_dev is not None:
                        play_audio(self.shutter_sound)
                        self.bus.emit(message.forward("neon.metric", {"name": "audio-response"}))
                        # LOG.debug(f"TIME: to_speak, {time.time()}, {message.data['utterance']}, {message.context}")
                        os.system(f"fswebcam -d {self.cam_dev} --delay 2 --skip 2 "
                                  f"-r 1280x720 --no-banner {newest_pic}")
                        time.sleep(1)
                        self.display_image(image=newest_pic)
                    else:
                        self.speak_dialog("NoCamera", private=True)
            except Exception as e:
                LOG.error(e)
            # finally:
            #     if ("user" or "my") in message.data.get("utterance"):
            #         self.save_user_info(newest_pic, "picture")

    @intent_handler('ShowLastIntent.intent')
    def handle_show_last_intent(self, message):
        if "picture" in message.data.get("utterance"):
            if request_from_mobile(message):
                pass
                # TODO
                # self.speak("MOBILE-INTENT LATEST_PICTURE")
                # self.mobile_skill_intent("show_pic", {}, message)
                # self.socket_io_emit('show_pic', '', message.context["flac_filename"])
            elif message.context.get("klat_data"):
                self.speak_dialog("ServerNotSupported", private=True)
            else:
                self.display_latest_pic(profile_pic=("user" or "my") in message.data.get("utterance"),
                                        requested_user=get_message_user(message))
        else:
            if request_from_mobile(message):
                pass
                # TODO
                # self.speak("MOBILE-INTENT LATEST_VIDEO")
                # self.mobile_skill_intent("show_vid", {}, message)
                # self.socket_io_emit('show_vid', '', message.context["flac_filename"])
            elif message.context.get("klat_data"):
                self.speak_dialog("ServerNotSupported", private=True)
            else:
                self.display_latest_vid(profile_vid=("user" or "my") in message.data.get("utterance"),
                                        requested_user=get_message_user(message))

    def display_latest_pic(self, secs=15, notify=True, profile_pic=False, requested_user="local"):
        try:
            latest_pic = get_most_recent_file_in_dir(os.path.join(self.pic_path, requested_user),
                                                     self.image_extension) if not profile_pic \
                else None  # self.preference_user()["picture"]
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
            latest_vid = get_most_recent_file_in_dir(os.path.join(self.vid_path, requested_user),
                                                     self.video_extension) if not profile_vid \
                else None  # self.preference_user()["video"]
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
            play_audio(self.notify_sound)

        # method of displaying image
        # if self.configuration_available["devVars"]["devType"] in ("pi", "neonPi"):
        #     os.system("sudo /home/pi/ngi_code/scripts/splash/splash_start " + image + " " + str(secs))
        if is_gui_installed():
            self.gui.show_image(image, fill="PreserveAspectFit")
        else:
            os.system("timeout " + str(secs) + " eog " + image)

    @intent_handler('TakeVidIntent.intent')
    def handle_take_vid_intent(self, message):
        if "video" in message.data.get("utterance"):
            try:
                duration = message.data["duration"]
                heard_duration = True
            except KeyError:
                duration = "5 seconds"
                heard_duration = False
                # if not message.context.get("klat_data") and not message.data.get("mobile"):
                #     self.speak_dialog("DefaultDuration", {"duration": duration}, private=True)

            if request_from_mobile(message):
                self.speak_dialog("LaunchCamera", private=True)
                # TODO
                # self.speak("MOBILE-INTENT VIDEO")
                # self.mobile_skill_intent("video", {}, message)
                # self.socket_io_emit('video', '', message.context["flac_filename"])
            elif message.context.get("klat_data"):
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
                if request_from_mobile(message):
                    # TODO
                    # self.mobile_skill_intent("video", {"duration": duration}, message)
                    # self.socket_io_emit('video', f'&duration={duration}', message.context["flac_filename"])
                    self.speak("LaunchCamera", private=True)
                elif message.context.get("klat_data"):
                    self.speak_dialog("ServerNotSupported", private=True)
                elif self.cam_dev:
                    if heard_duration:
                        self.speak_dialog("StartRecording", {"duration": duration}, private=True)
                    else:
                        self.speak_dialog("DefaultDuration", {"duration": duration}, private=True)
                    self.vidid += 1
                    play_audio(self.record_sound)
                    vid_path = os.path.join(self.vid_path, get_message_user(message))
                    if not os.path.exists(vid_path):
                        LOG.debug(f"Creating video path: {vid_path}")
                        os.makedirs(vid_path)

                    path = vid_path + "v" + str(self.vidid) + ".avi" if not\
                        ("user" or "my") in message.data.get("utterance") else \
                        vid_path + "user_video_v" + str(self.vidid) + ".avi"
                    os.system(f"streamer -f rgb24 -i {self.cam_dev} -t 00:00:{secs} -o {path}.avi")
                    play_audio(self.notify_sound)
                    # if ("user" or "my") in message.data.get("utterance"):
                    #     self.save_user_info(path, 'video')

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
        self.handle_camera_completed()
