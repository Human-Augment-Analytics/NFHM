# Vue Frontend for Biocosmos

The frontend portion of Biocosmos has been refactored to utilize Vue 3, written using Composition API. Please follow this document to help you 
understand the common pitfalls, and ease your development journey. Make sure you are using at least **npm version 18** when running anything.

## Table of Contents

- [Vue 3][#vue-3]
- [Vite](#vite)
  - [Using third party packages](#using-third-party-packages)
  - [Testing locally](#testing-locally)
  - [Build step](#build-step)
- [Creating New Components](#creating-new-components)
  - [Composition API](#composition-api)
  - [Injecting Components](#injecting-components)

## Vue 3

Vue 3 is a modern, fast and versatile framework for front end development. 

To learn more, visit https://vuejs.org/guide/introduction.html

## Vite 

Vite is the build tool used most commonly in Vue 3 development. It makes it easier to organize all third party packages used by the app, as well 
as ensuring the app is built quickly and with the least amount of settings-fiddling. 

Vite comes out of the box with support with everything you would need, like JSX, Typescript, ES6, etc.

To learn more, visit https://vite.dev/guide/

### Using third party packages

Previously using third party packages may be annoying, especially as a project's scope increased. For brevity's sake, all you need to remember is to 
add your required package to the `dependencies` section of your `frontend/package.json` file. 

You can either add it directly to the file, or run the specific command on your package manager of choice (e.g. `yarn add axios` or `npm install axios`)

example: 
```
... 

  "dependencies": {
    "axios": "^1.7.7",
    "sweetalert2": "^11.14.2",
    "vue": "^3.5.10"
  },
... 
```

If you added it manually, you can install all dependency packages for your app using your package manager's install command (e.g.`yarn install` or `npm install`). After installing the package(s), you should be able to see them in the frontend/node_modules directory, from which they will be accessed by your components.

(Debug Hint: if you are trying to change your package version on dependencies, remember to delete `yarn.lock` or `package-lock.json`, as these contain current builds of your package)

Once your packages are installed, you can import them in your .vue component files like so:

```
import axios from 'axios';
```

### Testing Locally

You do not necessarily need to run your entire .devcontainer if you want to just debug your frontend components that you're working on (as long as you don't require backend access). To develop and test your frontend app before building, make sure you ran your app install command (`yarn install` or `npm install`) then simply run 
`yarn run dev` if you have a `yarn.lock` file, or `npm run dev` if you have a `package-lock.json` file. This will allow you to work on the frontend components without needing to build the app every time. 

### Build step

**THIS IS A VERY IMPORTANT STEP** 

For the frontend component to work seemlessly with the rest of the app, you must remember to run the **build** command after you've completed your changes. 
The build command is either `yarn build` or `npm run build` (depending on your package manager of choice). This will create a recent build of the frontend app in the `frontend/dist/` directory, which contains the compiled and optimized production files for the app. This is the portion that will interact with the rest of the application running on the .devcontainer.

## Creating New Components

Unlike previous components written in .js, all components going forward will be written in .vue files. Components are used as logical chunks for an application, like building blocks that make up the app. If you are thinking of adding a new piece of functionality, you should make a new component for it. 

Examples: Search, Display, Dialog, etc. 

Components can easily pass information between each other using *emits*

### Composition API

Vue 3 has 2 standards of writing components: Options API and Composition API. To read more on the difference, read this: https://vueschool.io/articles/vuejs-tutorials/options-api-vs-composition-api/.

We will be writing most of our components in Composition API, but if you feel its easier to write in OptionsAPI, that's ok. As components are separate blocks that get compiled during the build process, you can write them in whichever standard works best for you!

### Injecting Components

Once you've completed your component, you can inject it in the HTML template of any other component. 

For example, if I create a component called `ItemDialog.vue`, I can simply insert it into `App.vue` by putting an HTML tag like `<item-dialog>`