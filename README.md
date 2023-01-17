# Maaldar  
<b>Maaldar</b> is a Nitro bot for Discord that gives nitro boosters for your server members a custom identity.  

## Roles  
Maaldar works with roles. You have your own role.  

### Set your name
<i>Set your role's name</i> <br />  
<img src="https://user-images.githubusercontent.com/24255685/174434022-3d129bcb-febb-4809-9773-2312d979e922.gif" width="400px" height="400px" />
### Set your role color
<i>Set your role's color with a hex value</i> <br />  
<img src="https://user-images.githubusercontent.com/24255685/174434144-0788e65b-2c75-47b7-b3dc-9f843c501872.gif" width="400px" height="400px" />

### Set your role icon
<i>Set your role's icon with any URL containing an image</i> <br />  
<img src="https://user-images.githubusercontent.com/24255685/174434274-c210b2bd-dede-41a6-8571-f916798e6f9a.gif" width="400px" height="400px" />

### Get a colour palette of your profile picture
<i>A palette containing the most vibrant colours from your profile picture</i> <br />  
<img src="https://user-images.githubusercontent.com/24255685/174434365-72f4707b-1293-471c-b7bc-44572ab5487d.gif" width="400px" height="400px" />

### Assign your role to someone else
<i>Give your role to your friend as well</i> <br />  
<img src="https://user-images.githubusercontent.com/24255685/174434433-6cdadd56-a9c8-4174-91c9-fb629ab8ec94.gif" width="400px" height="400px" />  

## Set your colour through a colour picker website  
<i>Set your colour role from a session-enabled colour picker website</i> <br />  
<img src="https://user-images.githubusercontent.com/24255685/174449804-06c21dee-8fcb-4c86-af4e-6511c964b472.gif" width="400px" height="400px" />


## Configuration
Fill <code>config.json</code> with the required information. <hr>
* `guild_id` contains the `integer` guild ID that you want your bot to work in.  
* `role_ids` contains all the `integer` role IDs that you want the commands to be used by
* `custom_role_id` contains the `integer` role ID below which the roles should be created and positioned
* `emoji_server_id` contains the `integer` guild ID where the emojis from palette command will be uploaded
* `connection_string` is connection the `string` (e.g postgresql://username:password@host:port/database_name)
* `token` is the `string` bot token
