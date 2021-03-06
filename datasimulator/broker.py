# -*- coding: utf-8 -*-
#
#  Author: Cayetano Benavent & Alberto Asuero, 2016.
#  www.geographica.gs
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#


import signal
import random
from time import sleep
from threading import active_count
from datetime import datetime
from proclauncher import ProcLauncher
from orioncontextbroker import OrionContextBroker
from orioncontextbrokerconfig import ocbrconfig



class UpdateAuthTokenException(Exception):
    pass

class UpdateSubscription(ProcLauncher):

    def workerLauncher(self, title):
        self.__newSubscrition()
        self.logger.info("Updated subscription successfully!")

    def __newSubscrition(self):
        json_data_subs = {
                "entities": [
                    {
                      "type": "geoEntTest",
                      "isPattern": "true",
                      "id": "10*"
                    }
                ],
                "attributes": [
                        "position","timeinstant","valor_01", "valor_02"
                ],
                "reference": ocbrconfig.get("url_sbc"),
                "duration": "P1M",
                "notifyConditions": [
                    {
                        "type": "ONCHANGE",
                        "condValues": [
                            "position","timeinstant","valor_01", "valor_02"
                        ]
                    }
                ],
                "throttling": "PT0S"
            }

        __auth_token, __exp_date = ctbr.getAuthToken(ssl=False)
        if not __auth_token:
            raise UpdateAuthTokenException("No Auth Token")
        udt = ctbr.postData(__auth_token, json_data_subs, "subscribe", ssl=False)
        # print(udt)

class UpdateTestProccess(ProcLauncher):

    def __updateAuthToken(self):
        try:
            self.__auth_token, self.__exp_date = ctbr.getAuthToken(ssl=False)
            self.logger.info("Auth_token successfully updated!. Expires at: {}".format(self.__exp_date))
            # print(self.__auth_token, self.__exp_date)

        except Exception as err:
            self.logger.error("UpdateAuthToken error: {}".format(err))

    def workerLauncher(self, title):
        try:
            self.logger.info("Starting update process...")

            self.__updateAuthToken()

            if self.__auth_token:
                self.__simulateQuery()
                self.__simulateUpdate()

            else:
                raise UpdateAuthTokenException("No Auth Token")

        except Exception as err:
            self.logger.error("UpdateTestProccess error: {}".format(err))

    def __simulateQuery(self):
        json_data_qry = {
                     "entities": [
                        {
                          "type": "geoEntTest",
                          "isPattern": "true",
                          "id": "10*"
                        }
                      ]
                    }

        qry = ctbr.postData(self.__auth_token, json_data_qry, "query", ssl=False)
        # print(qry)
        self.logger.info("Test query successfully!")

    def __simulateUpdate(self):
        list_ents = ["10025", "10026", "10027", "10028", "10029"]
        # list_ents = ["10025", "10026"]
        for ent in list_ents:
            json_data_udt = {
                "contextElements": [
                    {
                        "type": "geoEntTest",
                        "isPattern": "false",
                        "id": ent,
                        "attributes": [
                          {
                              "name": "timeinstant",
                              "type": "ISO8601",
                              "value": datetime.utcnow().isoformat()
                          },
                          {
                              "name": "valor_01",
                              "type": "string",
                              "value": round(random.random() * 10, 2)
                          },
                          {
                              "name": "valor_02",
                              "type": "string",
                              "value": round(random.random(), 2)
                          }
                        ]
                    }
                ],
                "updateAction": "UPDATE"
            }

            udt = ctbr.postData(self.__auth_token, json_data_udt, "update", ssl=False)
            # print(udt)
            self.logger.info("CartoDB and Orion update successfully for Entity: {}!".format(ent))
            sleep(0.1)

def signal_handler(signal, frame):
    for l in launchers:
        l.stop()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    fl_fw_auth = ocbrconfig.get("fl_fw_auth")
    url_authtk = ocbrconfig.get("url_authtk")
    url_qry = ocbrconfig.get("url_qry")
    url_udt = ocbrconfig.get("url_udt")
    url_sbc = ocbrconfig.get("url_sbc")
    serv_name = ocbrconfig.get("serv_name")
    subserv_name = ocbrconfig.get("subserv_name")

    ctbr = OrionContextBroker(fl_fw_auth, url_authtk, url_qry, url_udt, url_sbc, serv_name, subserv_name)

    # data simulator period: 15 seconds
    # update subscription period: 72000 seconds (20 hours)
    launchers = [UpdateSubscription("Update subscription", 72000, delay=0),
                 UpdateTestProccess("Simulator proccess", 15, delay=0)]

    for l in launchers:
        l.start()

    while active_count() > 1:
        sleep(0.1)
