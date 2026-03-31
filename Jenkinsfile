pipeline {
    agent any

    stages {

        stage('Install Package(s)') {
            steps {
                sh '''
                python3 -m pip install --upgrade pip
                python3 -m pip install -r requirements.txt
                '''
            }
        }

        stage('Syntax Check/PEP8'){
            steps {
                sh '''
                pylint netman_jenkins_obj2.py --fail-under=5
                '''
            }
        }

        stage('Running the Application'){
            steps {
                sh '''
                python3 netman_jenkins_obj2.py
                '''
            }
        }

        stage('Unit Test'){
            steps {
                sh '''
                python3 -m unittest unitTest.py -v
                '''
            }
        }
    }

    post {
        always {
            mail to: 'thfo7662@colorado.edu',
            subject: "Jenkins Build: ${currentBuild.currentResult}",
            body: "Build result: ${currentBuild.currentResult}"
        }
    }
}