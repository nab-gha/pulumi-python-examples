import pulumi
import unittest

class MyMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + '_id', args.inputs]
    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}

pulumi.runtime.set_mocks(MyMocks())

# It's important to import `infra` _after_ the mocks are defined.
import example_one


class TestingWithMocks(unittest.TestCase):

    # check 1: Instances have a Name tag.
    @pulumi.runtime.test
    def test_server_tags(self):
        def check_tags(args):
            urn, tags = args
            self.assertIsNotNone(tags, f'server {urn} must have tags')
            self.assertIn('Name', tags, 'server {urn} must have a name tag')

        return pulumi.Output.all(example_one.servers["frontend"][0].ServerComponent.instance, example_one.servers["frontend"][0].tags).apply(check_tags)

    # TODO(check 2): Instances must not use an inline userData script.
    # TODO(check 3): Instances must not have SSH open to the Internet.