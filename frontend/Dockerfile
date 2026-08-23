FROM nginx:alpine

RUN rm -rf /usr/share/nginx/html/*

COPY index.html team.html mockup.html styles.css cookie-notice.js /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/
COPY avatars/ /usr/share/nginx/html/avatars/
COPY nginx.conf /etc/nginx/conf.d/default.conf
