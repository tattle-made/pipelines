import luigi


class MockTask(luigi.Task):
    def output(self):
        return luigi.LocalTarget('mock.txt')

    def run(self):
        with self.output().open("w") as out_file:
            out_file.write("test")


if __name__ == "__main__":
    luigi.build([MockTask()])
