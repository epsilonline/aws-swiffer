<a name="readme-top"></a>

<div align="center">

  <img src="aws-swiffer.png" alt="logo" width="140"  height="auto" />
  <br/>

  <h3><b>AWS Swiffer</b></h3>

</div>

# 📗 Table of Contents

- [📖 About the Project](#about-project)
  - [🔑 Key Features](#key-features)
- [💻 Getting Started](#getting-started)
  - [⚒ Usage](#usage)
  - [📂 Folder structure](#folder-structure)
- [👥 Authors](#authors)
- [🔭 Future Features](#future-features)
- [🤝 Contributing](#contributing)

[//]: # (- [❓ FAQ]&#40;#faq&#41;)

# 📖 AWS Scripts <a name="about-project"></a>

> Cli for help you to delete aws resources

Made with care and love by the **_Epsilon Team_**.

## 🔑 Key Features <a name="key-features"></a>

> Helps perform **repetitive** and **complex** actions for delete AWS resources
>

- **Delete bucket**
- **Delete codebuild resources**
- **Delete codepipeline resources**
- **Delete EC2 Instances**
- **Delete ECS Resources**
- **Delete IAM Resources**

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## 💻 Getting Started <a name="getting-started"></a>

**Install**
```bash
chmod +x install.sh
./install.sh
aws-swiffer --help
```

**Install completion:**

```bash
aws-swiffer --install-completion zsh
```

For **zsh**, if completion not works add to ~/.zshrc this lines:
```bazaar
autoload -Uz compinit
zstyle ':completion:*' menu select
fpath+=~/.zfunc
compinit
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### ⚒️ Usage <a name="usage"></a>
```bash
aws-swiffer --help
aws-swiffer --profile profile-1 --region eu-west-2 remove-bucket-by-name
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### 📂 Folder Structure <a name="folder-structure"></a>

``` Bash
.
├── aws_swiffer
│   ├── command # Command functions
│   ├── factory # Factory for retrieve resourcs to delete
│   ├── __init__.py
│   ├── main.py
│   ├── __pycache__
│   ├── resources # Class for resources to delete
│   └── utils # Utils
├── aws-swiffer.png
├── install.sh
├── poetry.lock
├── pyproject.toml
├── README.md
└── tests

```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 👥 Authors <a name="authors"></a>

- **Gabriele Previtera**: [@jiin995](https://gitlab.com/jiin995) 

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🔭 Future Features <a name="futurecd-features"></a>

Add support for delete more resources with beautiful readme!

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->

## 🤝 Contributing <a name="contributing"></a>

If you like this project add more scripts

<p align="right">(<a href="#readme-top">back to top</a>)</p>

[//]: # (## ❓ FAQ <a name="faq"></a>)

[//]: # ()
[//]: # (> Add at least 2 questions new developers would ask when they decide to use your project.)

[//]: # ()
[//]: # (- **[Question_1]**)

[//]: # ()
[//]: # (  - [Answer_1])

[//]: # ()
[//]: # (- **[Question_2]**)

[//]: # ()
[//]: # (  - [Answer_2])

[//]: # ()
[//]: # (<p align="right">&#40;<a href="#readme-top">back to top</a>&#41;</p>)