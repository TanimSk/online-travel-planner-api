from rest_framework.permissions import BasePermission
from dj_rest_auth.registration.views import RegisterView
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Subquery, OuterRef, Sum, F
from django.utils import timezone

from .serializers import (
    AdminCustomRegistrationSerializer,
    RfqSerializer,
    ApprovalSerializer,
    VendorListSerializer,
    BasicRfqSerializer,
    AssignServiceSerializer,
    UpdateCommissionSerializer,
    EditPriceSerializer,
    BillServicesSerializer,
    BillPaySerializer,
    VendorCustomRegistrationSerializer,
    AgentSerializer,
    BillRequestSerializer,
    PaidBillSerializer,
)
from commons.serializers import CategorySerializer
from vendor.serializers import (
    RfqServiceSerializer,
    ManageServicesSerializer,
    DispatchBillServiceSerializer,
)

from agent.models import Rfq, RfqService, Agent
from commons.models import Bill
from commons.models import Category, User
from vendor.models import Vendor, VendorCategory, Service

from commons.send_email import (
    rfq_updated_agent,
    rfq_declined_agent,
    bill_request_agent,
    bill_pay_vendor,
    rfq_assigned_vendor,
)


# Authenticate Vendor Only Class
class AuthenticateOnlyAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_admin:
                return True
            else:
                return False
        return False


# Agent Registration
class AdminRegistrationView(RegisterView):
    serializer_class = AdminCustomRegistrationSerializer


# Vendor Registration
class VendorRegistrationView(RegisterView):
    serializer_class = VendorCustomRegistrationSerializer


# Pagination Config
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 12
    page_query_param = "p"


class OverviewAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, rfq_id=None, format=None, *args, **kwargs):
        quotes_reqs = Rfq.objects.filter(status="pending").count()
        list_orders = Rfq.objects.filter(status="confirmed").count()
        total_services = Service.objects.all().count()

        # pie chart
        completed_rfq = Rfq.objects.filter(status="completed").count()
        pie_chart = {
            "completed_rfq": completed_rfq,
            "requested_rfq": quotes_reqs,
            "confirmed_rfq": list_orders,
        }

        serialized_data_table = RfqSerializer(
            Rfq.objects.all().exclude(status="declined").order_by("-created_on"),
            many=True,
        )

        return Response(
            {
                "quotation_requests": quotes_reqs,
                "list_of_orders": list_orders,
                "total_services": total_services,
                "pie_chart": pie_chart,
                "rfq_status_table": serialized_data_table.data,
            }
        )


class CategoryAPI(APIView):
    serializer_class = CategorySerializer
    permission_classes = [AuthenticateOnlyAdmin]

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = CategorySerializer(data=request.data, many=True)

        if serialized_data.is_valid(raise_exception=True):
            for data in serialized_data.data:
                Category.objects.create(**data)
            return Response({"status": "Successfully created category"})


class PendingRfqAPI(APIView):
    serializer_class = RfqSerializer
    permission_classes = [AuthenticateOnlyAdmin]

    # Quotation Serializer
    def get(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            rfqs_instance = Rfq.objects.filter(status="pending").order_by("-created_on")
            serialized_data = RfqSerializer(rfqs_instance, many=True)
            return Response(serialized_data.data)

        rfqs_instance = get_object_or_404(Rfq, id=rfq_id, status="pending")
        serialized_data = RfqSerializer(rfqs_instance)
        return Response(serialized_data.data)

    # Approve or decline a RFQ
    def post(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            return Response({"error": "RFQ ID missing"})

        rfq_instance = get_object_or_404(Rfq, id=rfq_id)
        serialized_data = ApprovalSerializer(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            if serialized_data.data.get("approved"):
                status = "approved"
                service_instance = RfqService.objects.filter(
                    rfq_category__rfq=rfq_instance
                )

                # Sub-queries
                admin_commission_subquery = Service.objects.filter(
                    pk=OuterRef("service_id")
                ).values("admin_commission")[:1]

                agent_commission_subquery = RfqService.objects.filter(
                    pk=OuterRef("pk")
                ).values("rfq_category__rfq__agent__agent__commission")[:1]

                # Update
                service_instance.update(
                    admin_commission=Subquery(admin_commission_subquery),
                    agent_commission=Subquery(agent_commission_subquery),
                )

                # send_email
                rfq_updated_agent(rfq_instance=rfq_instance)

            else:
                status = "declined"
                rfq_declined_agent(rfq_instance=rfq_instance)

            rfq_instance.status = status
            rfq_instance.approved_on = timezone.now()
            rfq_instance.save()

            return Response({"status": f"Successfully {status}"})

    def put(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            return Response({"error": "RFQ ID missing"})

        total_price = 0

        serialized_data = EditPriceSerializer(data=request.data)
        if serialized_data.is_valid(raise_exception=True):
            rfq_service = RfqService.objects.get(
                id=serialized_data.data.get("service_id"),
                rfq_category__rfq_id=rfq_id,
            )

            rfq_service.service_price = serialized_data.data.get("service_price")
            rfq_service.save()

            # get all services price and get the total amount
            total_price = RfqService.objects.filter(
                rfq_category__rfq=rfq_service.rfq_category.rfq
            ).aggregate(
                service_price=Sum(
                    F("service_price")
                    + (F("admin_commission") * F("service_price") * 0.01)
                    + (F("agent_commission") * F("service_price") * 0.01)
                )
            )[
                "service_price"
            ]

            rfq_instance = Rfq.objects.get(id=rfq_service.rfq_category.rfq.id)
            rfq_instance.total_price = total_price
            rfq_instance.save()

            return Response({"status": "Successfully updated price"})


# TODO:
# Query service -> select service -> attach to foreign key


class ApprovedRfqAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, rfq_id=None, format=None, *args, **kwargs):
        if rfq_id is None:
            if request.GET.get("type") == "order":
                rfqs_instance = Rfq.objects.filter(status="confirmed").order_by(
                    "-created_on"
                )
            else:
                rfqs_instance = Rfq.objects.filter(status="approved").order_by(
                    "-created_on"
                )
            serialized_data = RfqSerializer(rfqs_instance, many=True)
            return Response(serialized_data.data)

        if request.GET.get("type") == "order":
            rfqs_instance = get_object_or_404(Rfq, id=rfq_id, status="confirmed")
        else:
            rfqs_instance = get_object_or_404(Rfq, id=rfq_id, status="approved")

        serialized_data = RfqSerializer(rfqs_instance)
        return Response(serialized_data.data)


# Manage Vendors
class VendorListAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, vendor_id=None, format=None, *args, **kwargs):
        if vendor_id is None:
            vendor_instances = Vendor.objects.filter(approved=True).order_by(
                "-added_on"
            )
            serialized_data = VendorListSerializer(vendor_instances, many=True)
        else:
            vendor_instances = Vendor.objects.get(id=vendor_id, approved=True)
            serialized_data = VendorListSerializer(vendor_instances)

        return Response(serialized_data.data)


# Get, approve and delete requested vendors
class RequestedVendorAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, vendor_id=None, format=None, *args, **kwargs):
        if vendor_id is None:
            vendor_instances = Vendor.objects.filter(
                approved=False, vendor__emailaddress__verified=True
            ).order_by("-added_on")
            serialized_data = VendorListSerializer(vendor_instances, many=True)
        else:
            vendor_instances = get_object_or_404(
                Vendor,
                id=vendor_id,
                approved=False,
                vendor__emailaddress__verified=True,
            )
            serialized_data = VendorListSerializer(vendor_instances)

        return Response(serialized_data.data)

    def post(self, request, vendor_id=None, format=None, *args, **kwargs):
        if vendor_id is None:
            return Response({"error": "Vendor id missing"})

        vendor_instance = get_object_or_404(Vendor, id=vendor_id, approved=False)
        vendor_instance.approved = True
        vendor_instance.save()
        return Response({"status": "Successfully approved"})

    def delete(self, request, vendor_id=None, format=None, *args, **kwargs):
        if vendor_id is None:
            return Response({"error": "Vendor id missing"})

        vendor_instance = get_object_or_404(Vendor, id=vendor_id, approved=False)
        get_object_or_404(User, vendor=vendor_instance).delete()
        return Response({"status": "Successfully removed vendor"})


class TaskListAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, format=None, *args, **kwargs):
        rfq_instances = (
            Rfq.objects.filter(
                status="assigned",
            )
            .distinct()
            .order_by("-assigned_on")
        )

        response_arr = []

        for rfq_instance in rfq_instances:
            obj_data = {}
            obj_data["rfq_details"] = RfqSerializer(rfq_instance).data

            services_instance = RfqService.objects.filter(
                rfq_category__rfq=rfq_instance
            )
            serialized_data = RfqServiceSerializer(services_instance, many=True)
            obj_data["services_details"] = serialized_data.data

            response_arr.append(obj_data)

        return Response(response_arr)


# --------------- Manage Services ---------------
# vendor services
# approve service, view unapproved/approved service,
class ManageVendorServicesAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]
    serializer_class = ManageServicesSerializer

    def get(self, request, service_id=None, format=None, *args, **kwargs):
        if service_id is None:
            approved = True if request.GET.get("approved") == "true" else False
            instance = Service.objects.filter(
                approved=approved, added_by_admin=False
            ).order_by("-created_on")
            serialized_data = self.serializer_class(instance, many=True)
            return Response(serialized_data.data)

        try:
            instance = Service.objects.get(id=service_id, added_by_admin=False)
            serialized_data = self.serializer_class(instance)

        except Service.DoesNotExist:
            return Response({"error": "Service not found"})

        return Response(serialized_data.data)

    def post(self, request, service_id=None, format=None, *args, **kwargs):
        if service_id is None:
            return Response({"error": "Service id is missing"})

        serialized_data = UpdateCommissionSerializer(data=request.data)
        if serialized_data.is_valid(raise_exception=True):
            instance = Service.objects.get(id=service_id, added_by_admin=False)
            instance.admin_commission = serialized_data.data.get("commission")
            instance.approved = True
            instance.save()
            # instance = Service.objects.get(id=service_id, added_by_admin=False)
            return Response({"status": "Service has been approved"})

    def delete(self, request, service_id=None, format=None, *args, **kwargs):
        if service_id is None:
            return Response({"error": "Service id is missing"})

        instance = Service.objects.get(id=service_id, added_by_admin=False)
        instance.delete()
        return Response({"status": "Successfully declined service"})

    # def put(self, request, service_id=None, format=None, *args, **kwargs):
    #     if service_id is None:
    #         return Response({"error": "Service id is missing"})

    #     serialized_data = UpdateCommissionSerializer(data=request.data)
    #     if serialized_data.is_valid(raise_exception=True):
    #         instance = Service.objects.get(id=service_id, added_by_admin=False)
    #         instance.admin_commission = serialized_data.data.get("commission")
    #         instance.save()
    #         return Response({"status": "Successfully updated commission"})


# admin services
class ManageServicesAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]
    serializer_class = ManageServicesSerializer

    def get(self, request, service_id=None, format=None, *args, **kwargs):
        if service_id is None:
            instance = Service.objects.filter(added_by_admin=True).order_by(
                "-created_on"
            )
            serialized_data = self.serializer_class(instance, many=True)
            return Response(serialized_data.data)
        try:
            instance = Service.objects.get(id=service_id, added_by_admin=True)
            serialized_data = self.serializer_class(instance)

        except Service.DoesNotExist:
            return Response({"error": "Service not found"})

        return Response(serialized_data.data)

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = self.serializer_class(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            service_data = serialized_data.data
            service_data.pop("category_id")
            category_id = serialized_data.data.get("category_id")

            # Check if Category exists
            if Category.objects.filter(id=category_id).exists():
                # Creating a category for a admin service (for tracing)
                vendor_category_instance = VendorCategory.objects.create(
                    category_id=category_id
                )
                Service.objects.create(
                    vendor_category=vendor_category_instance,
                    **service_data,
                    added_by_admin=True,
                    approved=True,
                )

            else:
                return Response({"error": "Category doesn't exist!"})

            return Response({"status": "Successfully created service"})


# Assign Agent
class AssignAgentAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, format=None, *args, **kwargs):
        is_assigned = False if request.GET.get("assigned") == "true" else True

        # individual unassigned/assigned RFQ
        if request.GET.get("id", None) is not None:
            data = {}

            rfq = Rfq.objects.get(
                id=int(request.GET.get("id")),
            )
            rfq_service_instance = RfqService.objects.filter(
                rfq_category__rfq_id=int(request.GET.get("id")),
                service__added_by_admin=True,
                service__vendor_category__vendor__isnull=is_assigned,
            )

            data["rfq"] = BasicRfqSerializer(rfq).data
            data["rfq_services"] = RfqServiceSerializer(
                rfq_service_instance, many=True
            ).data

            return Response(data)

        # Get rfq ids with `added_by_admin=true` service value and assigned vendor is null/not null
        rfq_instances = (
            RfqService.objects.filter(
                service__added_by_admin=True,
                rfq_category__rfq__status="confirmed",
                service__vendor_category__vendor__isnull=is_assigned,
            )
            .order_by("-id")
            .values("rfq_category__rfq_id")
            .distinct()
        )

        response_array = []
        for rfq_instance in rfq_instances:
            data = {}

            rfq = Rfq.objects.get(id=rfq_instance["rfq_category__rfq_id"])
            rfq_service_instance = RfqService.objects.filter(
                rfq_category__rfq_id=rfq_instance["rfq_category__rfq_id"],
                service__added_by_admin=True,
                service__vendor_category__vendor__isnull=is_assigned,
            )

            data["rfq"] = BasicRfqSerializer(rfq).data
            data["rfq_services"] = RfqServiceSerializer(
                rfq_service_instance, many=True
            ).data

            response_array.append(data)

        return Response(response_array)

    def post(self, request, service_id=None, format=None, *args, **kwargs):
        serialized_data = AssignServiceSerializer(data=request.data)

        if serialized_data.is_valid(raise_exception=True):
            # get rfq & vendor service with verification filter
            rfq_service_instance = RfqService.objects.get(
                id=serialized_data.data.get("rfq_service_id"),
                service__added_by_admin=True,
                rfq_category__rfq__status="confirmed",
            )

            vendor_instance = Vendor.objects.get(
                id=serialized_data.data.get("vendor_id"),
                approved=True,
            )

            # check for category repeatation, if exists then copy the model, attach and update
            # if not, then create category, then copy, attach, update
            # vendor_category = rfq_service_instance.service.vendor_category
            category_id = rfq_service_instance.service.vendor_category.category.id

            # Search Category
            vendor_category_instance = VendorCategory.objects.filter(
                vendor=vendor_instance, category_id=category_id
            )

            if vendor_category_instance.exists():
                # Check if the service already exists
                # if does then only update
                service_instance = Service.objects.filter(
                    vendor_category__vendor=vendor_instance,
                    tracking_id=rfq_service_instance.service.tracking_id,
                )

                if service_instance.exists():
                    # shift
                    rfq_service_instance.service = service_instance.first()
                    rfq_service_instance.save()
                    rfq_assigned_vendor(rfq_service_instance)

                    return Response(
                        {"status": "Successfully assigned service to vendor"}
                    )

                vendor_category_instance = vendor_category_instance.first()

            else:
                vendor_category_instance = VendorCategory.objects.create(
                    vendor=vendor_instance, category_id=category_id
                )

            with transaction.atomic():
                copied_service_instance = rfq_service_instance.service

                # dettach rfq from service
                rfq_service_instance.service = None
                rfq_service_instance.save()

                # copy the service
                copied_service_instance.pk = None
                copied_service_instance.save()

                # attach to vendor
                # print(copied_service_instance.pk)
                copied_service_instance.vendor_category = vendor_category_instance
                copied_service_instance.save()

                # assign
                rfq_service_instance.service = copied_service_instance
                rfq_service_instance.save()

                # email
                rfq_assigned_vendor(rfq_service_instance)

                # Assign Bill to Vendor
                bill_instance = Bill.objects.get(service=rfq_service_instance)
                bill_instance.vendor = vendor_instance.vendor
                bill_instance.save()

            return Response({"status": "Successfully assigned service to vendor"})


# Agent Bills
class AgentBillAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, format=None, *args, **kwargs):
        if request.GET.get("received") == "true":
            bills_instance = Bill.objects.filter(status_1="admin_paid").order_by(
                "-admin_paid_on"
            )
            serialized_data = BillServicesSerializer(bills_instance, many=True)
            return Response(serialized_data.data)

        bills_instance = Bill.objects.filter(status_1="admin_bill").order_by(
            "-created_on"
        )
        serialized_data = BillServicesSerializer(bills_instance, many=True)
        return Response(serialized_data.data)

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = DispatchBillServiceSerializer(data=request.data, many=True)

        if serialized_data.is_valid(raise_exception=True):
            for service in serialized_data.data:
                bill_instance = Bill.objects.get(
                    tracking_id=service.get("tracking_id", None),
                )
                bill_instance.status_1 = "agent_bill"
                bill_instance.agent_billed_on = timezone.now()
                bill_instance.save()
                bill_request_agent(bill_instance=bill_instance)

            return Response({"status": "Successfully requested for bill to agent"})


class VendorBillAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]

    def get(self, request, format=None, *args, **kwargs):
        if request.GET.get("paid") == "true":
            # list of paid bills
            bills_instance = Bill.objects.filter(status_2="vendor_paid").order_by(
                "-vendor_paid_on"
            )
            serialized_data = PaidBillSerializer(bills_instance, many=True)
            return Response(serialized_data.data)

        # list of bill requests with due payment
        bills_instance = (
            Bill.objects.filter(admin_due__gt=0)
            .exclude(status_2="vendor_bill")
            .order_by("-admin_billed_on")
        )
        serialized_data = BillRequestSerializer(bills_instance, many=True)
        return Response(serialized_data.data)

    def post(self, request, format=None, *args, **kwargs):
        serialized_data = BillPaySerializer(data=request.data, many=True)

        if serialized_data.is_valid(raise_exception=True):
            for service in serialized_data.data:
                bill_instance = Bill.objects.get(
                    tracking_id=service.get("tracking_id", None),
                )
                due_amount = bill_instance.admin_due - service.get("paid_amount")

                if due_amount < 0:
                    return Response(
                        {"error": "Paid amount cannot be greater than bill!"}
                    )

                bill_instance.admin_payment_type = service.get(
                    "admin_payment_type", None
                )
                bill_instance.admin_due = due_amount
                bill_instance.vendor_paid_on = timezone.now()
                bill_instance.status_2 = "vendor_paid"
                bill_instance.save()
                bill_pay_vendor(bill_instance=bill_instance)

                return Response({"status": "Successfully paid bills"})


# Agent List
class AgentListAPI(APIView):
    permission_classes = [AuthenticateOnlyAdmin]
    serializer_class = AgentSerializer

    def get(self, request, agent_id=None, format=None, *args, **kwargs):
        if agent_id is None:
            agents_instance = Agent.objects.filter(agent__emailaddress__verified=True)
            serialized_data = self.serializer_class(agents_instance, many=True)
            return Response(serialized_data.data)

        agents_instance = Agent.objects.get(
            agent__emailaddress__verified=True, id=agent_id
        )
        serialized_data = self.serializer_class(agents_instance)
        return Response(serialized_data.data)
