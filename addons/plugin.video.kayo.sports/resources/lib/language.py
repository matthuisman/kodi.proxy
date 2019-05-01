from matthuisman.language import BaseLanguage

class Language(BaseLanguage):
    ASK_USERNAME     = 30001
    ASK_PASSWORD     = 30002
    LOGIN_ERROR      = 30003
    ASSET_ERROR      = 30004
    SELECT_PROFILE   = 30005
    NO_PROFILE       = 30006
    SHOWS            = 30007
    SPORTS           = 30008
    NO_STREAM        = 30009
    STARTING_SOON    = 30010
    LIVE             = 30011
    FROM_START       = 30012
    SELECT_PROFILE   = 30013
    SHOW_HERO        = 30014
    SET_REMINDER     = 30015
    REMOVE_REMINDER  = 30016
    REMINDER_SET     = 30017
    REMINDER_REMOVED = 30018
    GAME_NOT_STARTED = 30019
    FROM_LIVE        = 30020
    WATCH            = 30021
    CLOSE            = 30022
    EVENT_STARTED    = 30023
    LIVE_PLAY_TYPE   = 30024
    HLS_REQUIRED     = 30025
    CHOOSE           = 30026
    PLAY_FROM        = 30027

_ = Language()