HEADERS = {
    'User-Agent': 'okhttp/3.10.0',
#    'User-Agent': 'au.com.foxsports.core.App/1.1.5 (Linux;Android 8.1.0) ExoPlayerLib/2.7.3',
}

SPORT_LOGO = 'https://resources.kayosports.com.au/production/sport-logos/1x1/{}.png?imwidth=320'
IMG_URL    = 'https://vmndims.kayosports.com.au/api/v2/img/{}?location={}&imwidth={}'
CLIENTID   = 'qjmv9ZvaMDS9jGvHOxVfImLgQ3G5NrT2'
CHANNELS_PANEL = 'yJbvNNbmxlD6'

FORMAT_HLS_FMP4     = 'hls-fmp4'
FORMAT_HLS_TS       = 'hls-ts'
FORMAT_DASH         = 'dash'
PROVIDER_AKAMAI     = 'AKAMAI'
PROVIDER_CLOUDFRONT = 'CLOUDFRONT'

PROVIDERS            = [PROVIDER_AKAMAI, PROVIDER_CLOUDFRONT]
SUPPORTED_FORMATS    = [FORMAT_HLS_TS, FORMAT_DASH]

PREFER_PROVIDER      = PROVIDERS[0]
PREFER_FORMAT        = SUPPORTED_FORMATS[0]

SERVICE_TIME = 270

FROM_CHOOSE = 0
FROM_LIVE   = 1
FROM_START  = 2
LIVE_PLAY_TYPES = [FROM_CHOOSE, FROM_LIVE, FROM_START]