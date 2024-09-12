server {
    server_name data-test.graphgenie.app;

    location / {
        proxy_pass https://10ay.online.tableau.com;
        proxy_set_header Host 10ay.online.tableau.com;
	proxy_ssl_name '10ay.online.tableau.com';
	proxy_set_header x-Forwarded-Host $host;
        proxy_set_header X-Real-IP $remote_addr;
	proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
	proxy_set_header Host '10ay.online.tableau.com';
	proxy_cookie_domain '10ay.online.tableau.com' 'data-test.graphgenie.app';
	proxy_buffering on;
	proxy_buffer_size 512k;
	proxy_buffers 100 512k;

	proxy_http_version 1.1;
	proxy_set_header Upgrade $http_upgrade;
	proxy_set_header Connection "upgrade";
    }

    # Optional: Redirect HTTP to HTTPS
    # if ($scheme != "https") {
    #    return 301 https://$host$request_uri;
    # }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/data-test.graphgenie.app/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/data-test.graphgenie.app/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}

server {
    server_name okta-test.graphgenie.app;

    location / {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
	proxy_cookie_domain ~.* okta-test.graphgenie.app;
	proxy_cookie_path ~.* /;
	add_header P3P 'CP="ALLDSP COR PSAa PSDa OURNOR ONL UNI COM NAV"';
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/okta-test.graphgenie.app/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/okta-test.graphgenie.app/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = okta-test.graphgenie.app) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name okta-test.graphgenie.app;
    return 404; # managed by Certbot


}
server {
    if ($host = data-test.graphgenie.app) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name data-test.graphgenie.app;
    #return 404; # managed by Certbot


}
