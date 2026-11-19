<template>
<app-footer class="Xpage-footer">
   <div class="footer-links">
      <a href="https://www.elex.is">About ELEXIS</a>
      <RouterLink :to="{ name: 'docs-intro' }">Help</RouterLink>
      <a href="mailto:info@elex.is">Contact us</a>
   </div>
   <div class="footer-logos">
      <div class="logolint">
         <a target="_blank"
               href="https://www.elex.is/"
               title="ELEXIS">
            <span class="elexislogo"/>
         </a>
         <span class="horizon-info">
            <span class="eulogo" />
This project has received funding from the European Union's Horizon 2020<br/>
research and innovation programme under grant agreement No 731015.

         </span>
      </div>
      <div class="version right ">
      <span style="display:inline-block;">Version:<br/>{{ version }}</span>
      <a style="margin-left:5px;"
      href="https://github.com/elexis-eu/lexonomy"
      title="GitHub"
      target="_blank">
      <span class="githublogo"/>

      </a>
      </div>
   </div>

   

   
</app-footer>
</template>

<script setup>
const version = import.meta.env.VITE_LEXONOMY_VERSION || 'dev'
</script>

<style>
      app-footer .footer-links {
         text-align: right;
         padding-bottom: 10px;
         padding-right: 20px;
      }
      app-footer .footer-links a {
         color: #004494;
         font-weight: 400;
         font-size: 14px;
         line-height: 18px;
         margin-left: 30px;
      }
      app-footer .footer-logos{
         padding: 15px 20px 50px 50px;
         background: #f0f8ff;
	border-top: 1px solid #004494;
      }
      app-footer .footer-copyright{
         font-weight: 300;
         padding: 15px 15px 30px 50px;
         background: #b8b8b8;
      }
      app-footer .logolint a {
         height: 30px;
         display: inline-block;
         vertical-align: middle;
      }
      app-footer .logolint a::after{
          height: 30px;
         display: inline-block;
         content: " ";
         border-right: 1px solid #fff;
         margin: 0 10px;
      }
      app-footer .version{
         font-weight: 100;
         color: #004494;
         font-size: x-small;
         line-height: 1.5em;
         text-align: right;
         position: relative;
         top: -20px;
      }
app-footer .horizon-info {
height: 30px;
display: inline-block;
vertical-align: middle;
color: #004494;
font-size: x-small;
line-height: 1.5em;
}
app-footer .horizon-info img {
height: 30px;
}
app-footer .elexislogo {
   width: 112px;
   height: 30px;
   background-image: url(/assets/img/logo_elexis.png);
   background-size: contain;
   display: inline-block;
   background-repeat: no-repeat;
}
app-footer .eulogo {
   width: 45px;
   height: 30px;
   background-image: url(/assets/img/logo_eu.png);
   float: left;
   margin-right: 5px;
   background-size: contain;
   display: inline-block;
   background-repeat: no-repeat;
}
app-footer .githublogo {
   width: 20px;
   height: 20px;
   background-image: url(/assets/img/github.png);
   background-size: contain;
   display: inline-block;
   background-repeat: no-repeat;
}
</style>
