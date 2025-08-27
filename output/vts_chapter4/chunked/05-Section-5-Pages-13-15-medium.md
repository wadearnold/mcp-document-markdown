# Section 5 (Pages 13-15)

**Chunk**: 1 of 1  
**Size**: medium (992 tokens)  
**Section Type**: content  
**Processing Priority**: 4  
**Recommended Model**: gpt-3.5-turbo (4K context)  
**Generated**: 2025-08-26T17:12:14.643932

---

## Processing Guidance

- Optimized for GPT-4 - suitable for detailed analysis
- Concise content - suitable for direct inclusion in prompts

---

Field
Description
deviceType
Device type.
Note:  The deviceType field corresponds to Field 125, 
Usage 2 – Dataset ID 01 - Token Device, which is described 
in the VisaNet Authorization-Only Online Messages – Technical 
Specifications.
Format: It is one of the following values:
l
UNKNOWN
l
MOBILE_PHONE, which is equivalent to value 01 in Field 125
l
TABLET, which is equivalent to value 02 in Field 125
l
WATCH
l
MOBILEPHONE_OR_TABLET, which is equivalent to value 04 in 
Field 125
l
PC
l
HOUSEHOLD_DEVICE
l
WEARABLE_DEVICE
l
AUTOMOBILE_DEVICE
deviceName
A readable name for the device. Ideally, the customer enters this 
name. It can be used to identify the device in customer support 
calls.
Example: My Work Phone
Format: String; Base64URL-encoded; UTF-8; max length 128 
characters.
deviceNumber
Device number.
Format: String; max length 13 characters.
osType
Type of operating system.
Format: It is one of the following values:
l
ANDROID
l
IOS
l
WINDOWS
l
BLACKBERRY
l
TIZEN
l
OTHER
osVersion
Version of the operating system running on the device.
Example: 4.4.4
Format: String; max length 32 characters.
Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
68
\n\nField
Description
osBuildID
Operating system build identifier.
Example: KTU84M
Format: String; max length 32 characters.
deviceIDType
Attribute indicating the source of the Device ID value.
Example: The source for Device ID (deviceID) could be 
SecureElement, TEE, or Derived
Format: String; max length 32 characters.
deviceManufacturer
Manufacturer of the device.
Example: Samsung
Format: String; max length 32 characters.
deviceBrand
Brand name of the device.
Example: Galaxy
Format: String; max length 32 characters.
deviceModel
model of the device.
Example: SGH-T999
Format: String; max length 32 characters.
deviceLocation
Obfuscated geographic location of the device. Initially, when 
provisioned, this contains the general location of the device. 
Information will be supplied with latitude/longitude rounded to the 
nearest whole digit.
Example: +37/-121
Format: String; max length 25 characters.
deviceIndex
The index number from Visa where the deviceID is stored. This is 
required for token device binding.
Format: Integer; max length 2 digits.
deviceIPAddressV4
(Optional) The IP address of the device at the time of the 
provisioning request, with the value represented in 
255.255.255.255 format. An octet (255) may be 1–3 digits in 
length but cannot contain any leading zeros.
Format: String; max length 15 characters.
locationSource
Source used to identify consumer location.
Format: It is one of the following values:
l
WIFI
l
CELLULAR
l
GPS
l
OTHER
Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
69
\n\nField
Description
tokenProtectionMethod
Method of token protection.
Format: It is one of the following values:
l
SOFTWARE
l
TRUSTED_EXECUTION_ENVIRONMENT
l
SECURE_ELEMENT
l
CLOUD
originalDeviceID
Device ID from the original provision. This field is populated only 
when performing token-for-token provisioning and can be used 
only in the following APIs:
l
Approve Provisioning
l
Approve Provisioning Stand-In Notification
l
Token Create Notification
Format: String; max length 48 characters.
originalDeviceType
Device type from the original provision. This field is populated only 
when performing token-for-token provisioning and can be used 
only in the following APIs:
l
Approve Provisioning
l
Approve Provisioning Stand-In Notification
l
Token Create Notification
Format: It is one of the following values:
l
UNKNOWN
l
MOBILE_PHONE
l
TABLET
l
WATCH
l
MOBILEPHONE_OR_TABLET
l
PC
l
HOUSEHOLD_DEVICE
l
WEARABLE_DEVICE
l
AUTOMOBILE_DEVICE
Visa Token Service – Issuer API Specifications (JSON)
Encrypted Payload Data Structures
27 March 2025
Visa Confidential
70
