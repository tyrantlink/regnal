#### method
##### exact
triggers if the text matches *exactly*, for example, an auto response with trigger `beans` will only trigger if the message is exactly beans

if the auto response matches with [regex](#regex_1), it will match with a regex fullmatch
##### contains
triggers if the trigger is anywhere within the message
##### regex
triggers using raw regex, this is different from [the regex option](#regex_1), as this method won't use the standard word delimitation that exact and contains use
##### mention
trigger is always a user id, triggers whenever a user is directly pinged in the text of a message
#### disabled
auto response will not trigger. used to disable a native auto response with an override, or temporarily disable an auto response without deleting it
#### trigger
the text used when checking auto responses, or a user id if the method is [mention](#mention)
#### response
the auto response response, or a link to the script repository if the auto response is a script
#### type
##### text
simply responds with the [response](#response) text
##### file
responds with a file hosted on the CrAPI servers, generally reserved for native auto responses
##### script
loads an executes a script at the file location given in the [response](#response)
##### deleted
this auto response has been deleted
#### weight
the weight of the auto response, when a single message triggers multiple auto responses, most auto responses are set to 1000, decrease this value to decrease the chance of it being chosen, and increase this value to increase it's chance
#### chance
chance to be respond if selected in the random selection. simple percentage, if it does not respond and there were other possible options, the pool will be rerolled.
#### ignore cooldown
auto responses with this enabled will always respond, regardless of server set cooldown. there are zero native responses that use this option, and people can use this to spam, so be warned
#### regex
interpret the trigger as a regex string, this is different from [the regex method](#regex), as this option does use standard word delimitation
#### nsfw
auto response will only respond in channels marked as age restricted, or nsfw
#### case sensitive
requires the exact case of the trigger and message to match
#### delete trigger
deletes the message that triggered the response after responding
#### user
restricts an auto response to a specific user, 
#### source
the original source of the auto response, for example if you clipped a youtube video, or it's a reference to something. not required, but recommended.