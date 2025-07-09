# Cisco Catalyst 9300 SNMP Monitor

This C# console application allows you to monitor a Cisco Catalyst 9300 switch using SNMP (Simple Network Management Protocol).

## Prerequisites

- .NET 6.0 SDK or later
- SNMP enabled on your Cisco Catalyst 9300 switch
- SNMP community string configured on the switch
- Network connectivity to the switch

## Features

- Get system description
- Get system uptime
- List network interfaces

## Building the Application

1. Open a terminal in the project directory
2. Run the following command:
   ```
   dotnet build
   ```

## Running the Application

1. Run the application using:
   ```
   dotnet run
   ```
2. Enter the switch's IP address when prompted
3. Enter the SNMP community string when prompted
4. Select operations from the menu to monitor the switch

## SNMP Configuration on Cisco Switch

To enable SNMP on your Cisco Catalyst 9300, use these commands in privileged EXEC mode:

```
conf t
snmp-server community YOUR_COMMUNITY_STRING RO
end
write memory
```

Replace `YOUR_COMMUNITY_STRING` with your desired community string.

## Security Note

This application uses SNMP v2c which sends community strings in clear text. For production environments, consider using SNMPv3 which provides authentication and encryption. 