# PAM-Manager
*nix PAM Manager - a graphical tool for managing Linux/Unix PAM (Pluggable Authentication Modules) configuration.

It does not aim to be a PAM module itself. It works on top of PAM configuration and provides GUI, data models, validation, templates and tools for working with individual PAM services, modules and security policies.

            GUI
             │
             ▼
       Policy model
             │
             ▼
   UnifiedConfigManager
             │
       ┌─────┴─────┐
       ▼           ▼
   PAM files    templates

Since a frequent cause of problems with PAM configuration is the lack of knowledge of the mentioned 
environment and the options it offers, for reasons of flexibility the entire configuration is divided 
into:
- Policy fragments, i.e. the configuration of individual PAM modules
- Policy elements, which can combine one or more fragments, but also insert individual services
- Services (files in the /etc/pam.d directory), which serve specific purposes, determined by the system
  or administrator
- Template - templates for basic configurations in areas of fragments, elements, services and bundles

            Service
               │
               ▼
         Policy element
               │
       ┌───────┴───────┐
       ▼               ▼
 Policy fragment    Service
  

The project is in the basic development phase, intended primarily for testing options and gradual expansion.
Therefore, its use is at your own risk for now, the implementation of PAM policies should be tested first 
on a test system. Full restore include installation of needed packages has not yet been tested
