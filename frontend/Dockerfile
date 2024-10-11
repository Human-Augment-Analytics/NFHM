FROM node:18 AS build

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install  

COPY . .

RUN yarn build

FROM nginx:alpine

COPY --from=build /app/dist /data

COPY site.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
